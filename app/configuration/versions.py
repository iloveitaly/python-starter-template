import inspect

from app import root

VERSIONS_FILE = root / ".service-versions"


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
