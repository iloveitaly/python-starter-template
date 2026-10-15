"""
Inspect versions of services used by the application that cannot be versioned directly. Version drift is a common cause
of extremely hard-to-debug issues, so we capture & check versions on test & in prod.
"""

import inspect
import json
import sys

from app.env import loose_env
from app.setup import get_root_path

VERSIONS_FILE = get_root_path() / ".service-versions"


def check_service_versions():
    """
    Production check & logging of versions.

    Chrome is excluded since it's not used in production
    """

    # import during execution to avoid circular imports
    from app import log

    persisted_versions = json.loads(VERSIONS_FILE.read_bytes())

    current_redis = redis_version()
    if current_redis != persisted_versions["redis"]:
        log.warning(
            "Redis version mismatch",
            expected=persisted_versions["redis"],
            got=current_redis,
        )

    current_postgres = postgres_version()
    if current_postgres != persisted_versions["postgres"]:
        log.warning(
            "Postgres version mismatch",
            expected=persisted_versions["postgres"],
            got=current_postgres,
        )

    # this can happen, mostly locally, if another process creates the venv from a sys python without us knowing
    current_python = python_version()
    if current_python != persisted_versions["python"]:
        log.warning(
            "python version mismatch",
            expected=persisted_versions["python"],
            got=current_python,
        )


def postgres_version() -> str:
    from app.configuration.database import get_engine

    import sqlalchemy as sa

    with get_engine().connect() as conn:
        pg_version = conn.execute(sa.text("SHOW server_version")).scalar()
        assert pg_version
        # Extract major.minor version from full version string
        pg_version = pg_version.split()[0]

    return pg_version


def redis_version() -> str:
    from app.configuration.redis import get_redis

    redis_info = get_redis().info()
    assert not inspect.isawaitable(redis_info), "Redis info should not be awaitable"
    redis_version = redis_info["redis_version"]

    return redis_version


def chrome_version() -> str:
    """
    Chromium build used for integration tests.

    `PLAYWRIGHT_CHROME_WS_ENDPOINT` is the compose playwright server, so the
    recorded version matches CI and every laptop. A local launch is only used
    when that endpoint is unset.
    """

    from playwright.sync_api import sync_playwright

    endpoint = loose_env.str("PLAYWRIGHT_CHROME_WS_ENDPOINT")

    with sync_playwright() as playwright:
        if endpoint:
            browser = playwright.chromium.connect(endpoint, timeout=30_000)
        else:
            browser = playwright.chromium.launch()

        version = browser.version
        browser.close()

    assert version
    return version


def python_version() -> str:
    """
    Get the current Python version as a string.
    """
    return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
