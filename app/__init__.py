"""
This file should be imported first in any application entrypoint.
"""

from pathlib import Path

import structlog

from .configuration.database import configure_database
from .configuration.debugging import configure_debugging
from .configuration.logging import configure_logger
from .configuration.sentry import configure_sentry
from .configuration.versions import check_service_versions
from .environments import python_environment
from .setup import configure_openai, get_root_path

root: Path

# must type manually, unfortunately :/
# https://www.structlog.org/en/21.3.0/types.html
log: structlog.stdlib.BoundLogger


def setup():
    if hasattr(setup, "complete") and getattr(setup, "complete", False):
        return

    global root, log

    root = get_root_path()
    log = configure_logger()

    configure_database()
    configure_openai()
    configure_sentry()
    configure_debugging()
    check_service_versions()

    log.info("application setup", environment=python_environment())

    setattr(setup, "complete", True)


# side effects are bad, but it's fun to do bad things
setup()
