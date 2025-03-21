"""
Logging is really important:

* High performance JSON logging in production
* All loggers, even plugin or system loggers, should route through the same formatter
* Structured logging everywhere
* Ability to easily set thread-local log context

References:

- https://github.com/replicate/cog/blob/2e57549e18e044982bd100e286a1929f50880383/python/cog/logging.py#L20
- https://github.com/apache/airflow/blob/4280b83977cd5a53c2b24143f3c9a6a63e298acc/task_sdk/src/airflow/sdk/log.py#L187
- https://github.com/kiwicom/structlog-sentry
- https://github.com/jeremyh/datacube-explorer/blob/b289b0cde0973a38a9d50233fe0fff00e8eb2c8e/cubedash/logs.py#L40C21-L40C42
"""

import logging
import os
import sys
import warnings
from typing import Any, MutableMapping, TextIO

import orjson
import structlog
import structlog.dev
from decouple import config
from starlette_context import context
from structlog.processors import ExceptionRenderer
from structlog.tracebacks import ExceptionDictTransformer
from structlog.typing import EventDict, ExcInfo
from typeid import TypeID

from app.constants import NO_COLOR

from activemodel import BaseModel
from sqlalchemy.orm.util import object_state

from ..environments import is_production, is_staging

_original_warnings_showwarning: Any = None


def _showwarning(
    message: Warning | str,
    category: type[Warning],
    filename: str,
    lineno: int,
    file: TextIO | None = None,
    line: str | None = None,
) -> Any:
    """
    Redirects warnings to structlog so they appear in task logs etc.

    Implementation of showwarnings which redirects to logging, which will first
    check to see if the file parameter is None. If a file is specified, it will
    delegate to the original warnings implementation of showwarning. Otherwise,
    it will call warnings.formatwarning and will log the resulting string to a
    warnings logger named "py.warnings" with level logging.WARNING.
    """
    if file is not None:
        if _original_warnings_showwarning is not None:
            _original_warnings_showwarning(
                message, category, filename, lineno, file, line
            )
    else:
        log = structlog.get_logger(logger_name="py.warnings")
        log.warning(
            str(message), category=category.__name__, filename=filename, lineno=lineno
        )


def redirect_showwarnings():
    global _original_warnings_showwarning

    if _original_warnings_showwarning is None:
        _original_warnings_showwarning = warnings.showwarning
        # Capture warnings and show them via structlog
        warnings.showwarning = _showwarning


def pretty_traceback_exception_formatter(sio: TextIO, exc_info: ExcInfo) -> None:
    """
    By default, rich and then better-exceptions is used to render exceptions when a ConsoleRenderer is used.

    I prefer pretty-traceback, so I've added a custom processor to use it.

    https://github.com/hynek/structlog/blob/66e22d261bf493ad2084009ec97c51832fdbb0b9/src/structlog/dev.py#L412
    """

    # only available in dev
    from pretty_traceback.formatting import exc_to_traceback_str

    _, exc_value, traceback = exc_info
    formatted_exception = exc_to_traceback_str(exc_value, traceback, color=not NO_COLOR)  # type: ignore
    sio.write("\n" + formatted_exception)


def logger_name(logger: Any, method_name: Any, event_dict: EventDict) -> EventDict:
    """
    structlog does not have named loggers, so we roll our own

    >>> structlog.get_logger(logger_name="my_logger_name")
    """

    if logger_name := event_dict.pop("logger_name", None):
        # `logger` is a special key that structlog treats as the logger name
        # look at `structlog.stdlib.add_logger_name` for more information
        event_dict.setdefault("logger", logger_name)

    return event_dict


def log_processors_for_environment() -> list[structlog.types.Processor]:
    if is_production() or is_staging():

        def orjson_dumps_sorted(value, *args, **kwargs):
            "sort_keys=True is not supported, so we do it manually"
            # kwargs includes a default fallback json formatter
            return orjson.dumps(
                # starlette-context includes non-string keys (enums)
                value,
                option=orjson.OPT_SORT_KEYS | orjson.OPT_NON_STR_KEYS,
                **kwargs,
            )

        return [
            # add exc_info=True to a log and get a full stack trace attached to it
            structlog.processors.format_exc_info,
            # simple, short exception rendering in prod since sentry is in place
            # https://www.structlog.org/en/stable/exceptions.html this is a customized version of dict_tracebacks
            ExceptionRenderer(
                ExceptionDictTransformer(
                    show_locals=False,
                    use_rich=False,
                    # number of frames is completely arbitrary
                    max_frames=5,
                    # TODO `suppress`?
                )
            ),
            # in prod, we want logs to be rendered as JSON payloads
            structlog.processors.JSONRenderer(serializer=orjson_dumps_sorted),
        ]

    return [
        structlog.dev.ConsoleRenderer(
            colors=not NO_COLOR,
            exception_formatter=pretty_traceback_exception_formatter,
        )
    ]


def add_fastapi_context(
    logger: logging.Logger,
    method_name: str,
    event_dict: MutableMapping[str, Any],
) -> MutableMapping[str, Any]:
    """
    Take all state added to starlette-context and add to the logs

    https://github.com/tomwojcik/starlette-context/blob/master/example/setup_logging.py
    """
    if context.exists():
        event_dict.update(context.data)
    return event_dict


def simplify_activemodel_objects(
    logger: logging.Logger,
    method_name: str,
    event_dict: MutableMapping[str, Any],
) -> MutableMapping[str, Any]:
    """
    Make the following transformations to the logs:

    - Convert keys ('object') whose value inherit from activemodel's BaseModel to object_id=str(object.id)
    - Convert TypeIDs to their string representation object=str(object)

    What's tricky about this method, and other structlog processors, is they are run *after* a response
    is returned to the user. So, they don't error out in tests and it doesn't impact users. They do show up in Sentry.
    """
    for key, value in list(event_dict.items()):
        if isinstance(value, BaseModel):

            def get_field_no_refresh(instance, field_name):
                """
                This was a hard-won little bit of code: in fastapi, this action happens *after* the
                db session dependency has finished, which means the session is closed.

                If a DB operation within the session causes the model to be marked as stale, then this will trigger
                a `sqlalchemy.orm.exc.DetachedInstanceError` error. This logic pulls the cached value from the object
                which is better for performance *and* avoids the error.
                """
                return str(object_state(instance).dict.get(field_name))

            # TODO this will break as soon as a model doesn't have `id` as pk
            event_dict[f"{key}_id"] = get_field_no_refresh(value, "id")
            del event_dict[key]

        elif isinstance(value, TypeID):
            event_dict[key] = str(value)

    return event_dict


# order here is not particularly informed
PROCESSORS: list[structlog.types.Processor] = [
    # although this is stdlib, it's needed, although I'm not sure entirely why
    structlog.stdlib.add_log_level,
    structlog.contextvars.merge_contextvars,
    logger_name,
    add_fastapi_context,
    simplify_activemodel_objects,
    structlog.processors.TimeStamper(fmt="iso", utc=True),
    # add `stack_info=True` to a log and get a `stack` attached to the log
    structlog.processors.StackInfoRenderer(),
    *log_processors_for_environment(),
]


def _get_log_level():
    log_level = config("LOG_LEVEL", default="INFO", cast=str)
    return logging.getLevelNamesMapping()[log_level.upper()]


def _logger_factory():
    """
    Allow dev users to redirect logs to a file using PYTHON_LOG_PATH

    In production, optimized for speed (https://www.structlog.org/en/stable/performance.html)
    """

    if is_production() or is_staging():
        return structlog.BytesLoggerFactory()

    # allow user to specify a log in case they want to do something meaningful with the stdout

    if python_log_path := config("PYTHON_LOG_PATH", default=None):
        python_log = open(python_log_path, "a", encoding="utf-8")
        return structlog.PrintLoggerFactory(file=python_log)

    else:
        return structlog.PrintLoggerFactory()


def reset_stdlib_logger(
    logger_name: str, default_structlog_handler, level_override=None
):
    std_logger = logging.getLogger(logger_name)
    std_logger.propagate = False
    std_logger.handlers = []
    std_logger.addHandler(default_structlog_handler)

    if level_override:
        std_logger.setLevel(level_override)


def redirect_stdlib_loggers():
    """
    Redirect all standard logging module loggers to use the structlog configuration.

    Inspired by: https://gist.github.com/nymous/f138c7f06062b7c43c060bf03759c29e
    """
    from structlog.stdlib import ProcessorFormatter

    level = _get_log_level()

    # Create a handler for the root logger
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    # TODO I don't understand why we can't use a processor stack as-is here. Need to investigate further.

    # Use ProcessorFormatter to format log records using structlog processors
    formatter = ProcessorFormatter(
        processors=[
            # required to strip extra keys that the structlog stdlib bindings add in
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            PROCESSORS[-1]
            if not is_production() and not is_staging()
            # don't use ORJSON here, as the stdlib formatter chain expects a str not a bytes
            else structlog.processors.JSONRenderer(sort_keys=True),
        ],
        # processors unique to stdlib logging
        foreign_pre_chain=[
            # logger names are not supported when not using structlog.stdlib.LoggerFactory
            # https://github.com/hynek/structlog/issues/254
            structlog.stdlib.add_logger_name,
            # omit the renderer so we can implement our own
            *PROCESSORS[:-1],
        ],
    )
    handler.setFormatter(formatter)

    # Configure the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers = [handler]  # Replace existing handlers with our handler

    # Disable propagation to avoid duplicate logs
    root_logger.propagate = True

    # TODO there is a JSON-like format that can be used to configure loggers instead :/
    std_logging_configuration = {
        "httpcore": {},
        "httpx": {
            "levels": {
                "INFO": "WARNING",
            }
        },
        "azure.core.pipeline.policies.http_logging_policy": {
            "levels": {
                "INFO": "WARNING",
            }
        },
    }
    """
    These loggers either:

    1. Are way too chatty by default
    2. Setup before our logging is initialized

    This configuration allows us to easily override various loggers as we add additional complexity to the application
    """

    # now, let's handle some loggers that are probably already initialized with a handler
    for logger_name, logger_config in std_logging_configuration.items():
        reset_stdlib_logger(
            logger_name,
            handler,
            logger_config.get("levels", {}).get(logging.getLevelName(level)),
        )

    # TODO do i need to setup exception overrides as well?
    # https://gist.github.com/nymous/f138c7f06062b7c43c060bf03759c29e#file-custom_logging-py-L114-L128
    if sys.excepthook != sys.__excepthook__:
        logging.getLogger(__name__).warning("sys.excepthook has been overridden.")


def silence_loud_loggers():
    # unless we are explicitly debugging asyncio, I don't want to hear from it
    if not config("PYTHONASYNCIODEBUG", cast=bool, default=False):
        logging.getLogger("asyncio").setLevel(logging.WARNING)

    # TODO httpcore, httpx, urlconnection, etc


def configure_logger():
    """
    Create a struct logger with some special additions:

    >>> with log.context(key=value):
    >>>    log.info("some message")

    >>> log.local(key=value)
    >>> log.info("some message")
    >>> log.clear()
    """

    redirect_stdlib_loggers()
    redirect_showwarnings()
    silence_loud_loggers()

    # PYTEST_CURRENT_TEST is set by pytest to indicate the current test being run
    # Don't cache the loggers during tests, it make it hard to capture them
    cache_logger_on_first_use = "PYTEST_CURRENT_TEST" not in os.environ

    structlog.configure(
        cache_logger_on_first_use=cache_logger_on_first_use,
        wrapper_class=structlog.make_filtering_bound_logger(_get_log_level()),
        # structlog.stdlib.LoggerFactory is the default, which supports `structlog.stdlib.add_logger_name`
        logger_factory=_logger_factory(),
        processors=PROCESSORS,
    )

    log = structlog.get_logger()

    # context manager to auto-clear context
    log.context = structlog.contextvars.bound_contextvars
    # set thread-local context
    log.local = structlog.contextvars.bind_contextvars
    # clear thread-local context
    log.clear = structlog.contextvars.clear_contextvars

    return log
