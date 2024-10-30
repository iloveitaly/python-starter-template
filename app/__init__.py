"""
This file should be imported first in any application entrypoint.
"""

from pathlib import Path

import structlog

from .configuration.sentry import configure_sentry
from .environments import is_development, python_environment
from .setup import configure_logger, configure_openai, get_root_path

# must type manually, unfortunately :/
# https://www.structlog.org/en/21.3.0/types.html
log: structlog.stdlib.BoundLogger


def setup():
    if hasattr(setup, "complete") and setup.complete:
        return

    global root, log

    root = get_root_path()
    log = configure_logger()

    configure_openai()
    configure_sentry()

    log.info("application setup", environment=python_environment())

    setup.complete = True


# side effects are bad, but it's fun to do bad things
setup()
