"""
Test redis and postgres versions, must be done separately from chrome because of async event loop
"""

import json

from app.configuration.versions import (
    VERSIONS_FILE,
    postgres_version,
    redis_version,
)


def test_redis_version_matches():
    persisted_chrome_version = json.loads(VERSIONS_FILE.read_bytes())["redis"]

    assert persisted_chrome_version == redis_version()


def test_postgres_version_matches():
    persisted_chrome_version = json.loads(VERSIONS_FILE.read_bytes())["postgres"]

    assert persisted_chrome_version == postgres_version()
