"""
Inspect versions of services used by the application that cannot be versioned directly. Version drift is a common cause
of extremely hard-to-debug issues, so we capture & check versions on test & in prod.
"""

import inspect
import json
import sys
from collections.abc import Callable

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

    current_redis = _retry_while_unreachable(redis_version)
    if current_redis != persisted_versions["redis"]:
        log.warning(
            "Redis version mismatch",
            expected=persisted_versions["redis"],
            got=current_redis,
        )

    current_postgres = _retry_while_unreachable(postgres_version)
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


def _retry_while_unreachable(probe: Callable[[], str]) -> str:
    """
    Run a version probe, retrying briefly while the service is unreachable.

    This runs on every boot, and is the first thing in setup() that dials Redis and Postgres. On platforms with private
    DNS (Railway's `*.railway.internal`), names are not guaranteed to resolve the instant a container starts, so an
    unlucky boot died with `Error 8 connecting to redis.railway.internal:6379. nodename nor servname provided`.

    Only connection errors are retried, and the last one is re-raised, so a misconfigured or down service still fails
    the boot, just not on the first attempt.
    """

    import redis
    from tenacity import (
        retry,
        retry_if_exception_type,
        stop_after_delay,
        wait_exponential,
    )

    from app import log

    import sqlalchemy as sa

    return retry(
        retry=retry_if_exception_type(
            (
                OSError,
                redis.ConnectionError,
                redis.TimeoutError,
                sa.exc.OperationalError,
            )
        ),
        stop=stop_after_delay(30),
        wait=wait_exponential(max=5),
        before_sleep=lambda state: log.warning(
            "service unreachable, retrying version check",
            probe=probe.__name__,
            attempt=state.attempt_number,
            error=str(state.outcome.exception()) if state.outcome else None,
        ),
        reraise=True,
    )(probe)()


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
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch()
        return browser.version


def python_version() -> str:
    """
    Get the current Python version as a string.
    """
    return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
