import os
import typing as t

from decouple import config


def python_environment():
    return t.cast(str, config("PYTHON_ENV", default="development", cast=str)).lower()


def is_testing():
    return python_environment() == "test"


def is_local_testing():
    """
    Are tests being run outside of a CI environment?

    For determining when to auto-build javascript assets when running integration tests locally
    """

    # TODO sys.platform != "darwin"?

    return is_testing() and config("CI", default=False, cast=bool) is False


def is_integration_testing():
    """
    Are we running integration tests?

    Integration tests spawn a separate python process to run the fastapi server alongside the
    pytest instance and playwright process.

    This is helpful for enabling additional integrations which you don't want enabled during
    unit tests or local development. For instance, Posthog integration.
    """
    return is_testing() and "PYTEST_INTEGRATION_TESTING" in os.environ


def is_debug_logging():
    """
    Are we debug level or lower?

    Useful for automatically enabling debug mode in various external libraries
    """

    # TODO need to implement with the latest structlog stuff
    pass


def is_production():
    return python_environment() == "production"


def is_staging():
    return python_environment() == "staging"


def is_preview():
    """
    Preview environments are distinct from staging in that they are throwaway environments tied to a single PR
    """

    return python_environment() == "preview"


def is_productionish():
    """
    Is this environment production-like, meaning production, staging, or preview
    """

    return is_production() or is_staging() or is_preview()


def is_development():
    return python_environment() == "development"


def is_job_monitor():
    "is this the production flower application"
    # TODO should use a ENV var for app name, rather than hardcoding; how we determine & store container names needs to be refactored
    # TODO this is an azure-specific ENV var, we should use a more generic one?
    return config("CONTAINER_APP_NAME", default="", cast=str) == "prod-jmon"


def is_pytest():
    """
    PYTEST_CURRENT_TEST is set by pytest to indicate the current test being run
    """
    return "PYTEST_CURRENT_TEST" in os.environ


def is_alembic_migration():
    """
    Returns True if the code is running inside an active Alembic migration process.
    """

    return os.environ.get("ALEMBIC_MIGRATION", "false").lower() == "true"
