"""
Python initialization entrypoint. This is always run when any part of the app is imported.

It should run all configuration which requires any state (services, ENV, etc) so we get an immediate failure on startup.
This ensures that a deploy does not go out which fails *after* the health probes succeed.
"""

from pathlib import Path

from structlog_config import LoggerWithContext, configure_logger

from . import constants  # import all constants to trigger build failures
from .configuration.database import configure_database, run_migrations
from .configuration.debugging import configure_debugging
from .configuration.emailer import configure_mailer
from .configuration.lang import configure_python
from .configuration.openai import configure_openai
from .configuration.patches import configure_patches
from .configuration.posthog import configure_posthog
from .configuration.sentry import configure_sentry
from .configuration.signals import configure_signals
from .configuration.versions import check_service_versions
from .environments import (
    is_productionish,
    python_environment,
)
from .setup import get_root_path

root: Path
log: LoggerWithContext


def setup():
    if getattr(setup, "complete", False):
        return

    global root, log

    root = get_root_path()

    # log configuration should go first, so any logging is properly outputted downstream
    log = configure_logger(
        install_exception_hook=is_productionish(),
        json_logger=is_productionish(),
        # prevents any additional reconfiguration, which could cause issues with tests/dev
        finalize_configuration=is_productionish(),
    )

    # explicitly order configuration execution in case there are dependencies
    configure_python()
    configure_database()
    configure_openai()
    configure_sentry()
    configure_debugging()
    configure_mailer()
    check_service_versions()
    configure_patches()
    configure_posthog()
    configure_signals()

    log.info(
        "application setup",
        environment=python_environment(),
        build=constants.BUILD_COMMIT,
    )

    setattr(setup, "complete", True)

    # run migrations *after* setup is marked as complete, in case any migration logic depends on setup being complete
    # TODO I wonder if this will cause issues with the system not picking up on required DB changes? We will see
    if is_productionish():
        run_migrations()


# side effects are bad, but it's fun to do bad things
setup()

# after configuration is complete, import all models and commands to ensure there are no startup issues
# NOTE jobs are excluded since they are not required in all process types
from . import commands, models  # noqa: F401, E402
