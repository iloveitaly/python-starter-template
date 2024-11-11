"""
Logging is really important:

* High performance JSON logging in production
* All loggers should route through the same formatter
* Structured logging everywhere
* Ability to easily set thread-local log context
"""

import logging
import sys

import orjson
import structlog
import structlog.dev
from decouple import config

from ..environments import is_production

if is_production():
    RENDERER = structlog.processors.JSONRenderer(serializer=orjson.dumps)
else:
    RENDERER = structlog.dev.ConsoleRenderer()

PROCESSORS = [
    structlog.contextvars.merge_contextvars,
    structlog.processors.add_log_level,
    structlog.processors.format_exc_info,
    structlog.processors.TimeStamper(fmt="iso", utc=True),
    RENDERER,
]


def _get_log_level():
    log_level = config("LOG_LEVEL", default="INFO", cast=str)
    level = getattr(logging, log_level.upper())
    return level


def _logger_factory():
    """
    Allow dev users to redirect logs to a file using PYTHON_LOG_PATH

    In production, optimized for speed (https://www.structlog.org/en/stable/performance.html)
    """

    if is_production():
        return structlog.BytesLoggerFactory()

    logger_factory = structlog.PrintLoggerFactory()

    # allow user to specify a log in case they want to do something meaningful with the stdout
    if python_log_path := config("PYTHON_LOG_PATH", default=None):
        python_log = open(python_log_path, "a", encoding="utf-8")
        logger_factory = structlog.PrintLoggerFactory(file=python_log)

    return logger_factory


def redirect_stdlib_loggers():
    """
    Redirect all standard logging module loggers to use the structlog configuration.
    """
    from structlog.stdlib import ProcessorFormatter

    level = _get_log_level()

    # Create a handler for the root logger
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    # Use ProcessorFormatter to format log records using structlog processors
    formatter = ProcessorFormatter(
        processor=RENDERER,
        foreign_pre_chain=PROCESSORS[:-1],  # Exclude the renderer from the pre-chain
    )
    handler.setFormatter(formatter)

    # Configure the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers = [handler]  # Replace existing handlers with our handler

    # Disable propagation to avoid duplicate logs
    root_logger.propagate = True


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

    log = structlog.get_logger()

    # context manager to auto-clear context
    log.context = structlog.contextvars.bound_contextvars
    # set thread-local context
    log.local = structlog.contextvars.bind_contextvars
    # clear thread-local context
    log.clear = structlog.contextvars.clear_contextvars

    structlog.configure(
        cache_logger_on_first_use=True,
        wrapper_class=structlog.make_filtering_bound_logger(_get_log_level()),
        logger_factory=_logger_factory(),
        processors=PROCESSORS,
    )

    return log
