import logging

import orjson
import structlog
import structlog.dev
from decouple import config

from ..environments import is_production


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


def configure_logger():
    """
    Create a struct logger with some special additions:

    with log.context(key=value):
        log.info("some message")

    log.local(key=value)
    log.info("some message")
    log.clear()
    """

    log = structlog.get_logger()

    # context manager to auto-clear context
    log.context = structlog.contextvars.bound_contextvars
    # set thread-local context
    log.local = structlog.contextvars.bind_contextvars
    # clear thread-local context
    log.clear = structlog.contextvars.clear_contextvars

    log_level = config("LOG_LEVEL", default="INFO", cast=str)
    level = getattr(logging, log_level.upper())

    # we need this option to be set for other non-structlog loggers
    logging.basicConfig(level=level)

    structlog.configure(
        cache_logger_on_first_use=True,
        wrapper_class=structlog.make_filtering_bound_logger(level),
        logger_factory=_logger_factory(),
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.format_exc_info,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            (
                structlog.dev.ConsoleRenderer()
                if not is_production()
                else structlog.processors.JSONRenderer(serializer=orjson.dumps)
            ),
        ],
    )

    return log
