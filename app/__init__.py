"""
- This file is automatically imported when any module is imported
- It should run all configuration which requires any state (services, ENV, etc) so we get an immediate failure on startup
"""

from pathlib import Path

from structlog_config import LoggerWithContext, configure_logger

from . import constants  # noqa: F401, import all constants to trigger build failures
from .configuration.database import configure_database
from .configuration.debugging import configure_debugging
from .configuration.emailer import configure_mailer
from .configuration.lang import configure_python
from .configuration.openai import configure_openai
from .configuration.sentry import configure_sentry
from .configuration.versions import check_service_versions
from .environments import python_environment
from .setup import get_root_path

root: Path
log: LoggerWithContext


def setup():
    if hasattr(setup, "complete") and getattr(setup, "complete", False):
        return

    global root, log

    root = get_root_path()

    # log configuration should go first, so any logging is properly outputted downstream
    log = configure_logger()

    configure_python()
    configure_database()
    configure_openai()
    configure_sentry()
    configure_debugging()
    configure_mailer()
    check_service_versions()

    log.info("application setup", environment=python_environment())

    setattr(setup, "complete", True)


# side effects are bad, but it's fun to do bad things
setup()
