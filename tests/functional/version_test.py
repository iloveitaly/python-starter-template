"""
The service versions that we don't control through code are persisted to .service-versions.

We test to ensure the version used here matches the persisted version.

Why? Chrome version changes often break integration tests in unpredictable ways, so we want to make any version
drift intentional. The chance of this happening with redis or postgres is slim, but it doesn't hurt to enforce
version alignment to reduce the risk of weird bugs occurring because of version drift.
"""

import json

from app.configuration.versions import (
    VERSIONS_FILE,
    chrome_version,
    postgres_version,
    redis_version,
)

VERSION_ERROR = "Service version mismatch for {}, run 'uv run python -m app.cli write-versions' to update"


def test_redis_version_matches():
    persisted_chrome_version = json.loads(VERSIONS_FILE.read_bytes())["redis"]

    assert persisted_chrome_version == redis_version(), VERSION_ERROR.format("redis")


def test_postgres_version_matches():
    persisted_chrome_version = json.loads(VERSIONS_FILE.read_bytes())["postgres"]

    assert persisted_chrome_version == postgres_version(), VERSION_ERROR.format(
        "postgres"
    )


# def test_chrome_version_matches_persisted_version():
#     persisted_chrome_version = json.loads(VERSIONS_FILE.read_bytes())["chrome"]

#     assert persisted_chrome_version == chrome_version(), VERSION_ERROR.format("chrome")
