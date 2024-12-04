"""
Inspect versions of services used by the application that cannot be versioned directly. Version drift is a common cause
of extremely hard-to-debug issues, so we capture & check versions on test & in prod.
"""

import inspect
import json

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


def postgres_version() -> str:
    import sqlalchemy as sa

    from app.configuration.database import get_engine

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
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch()
        return browser.version
