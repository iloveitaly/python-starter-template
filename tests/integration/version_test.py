"""
The chrome version is persisted to .service-versions. We test to ensure the version used here matches the persisted version.

Why? Chrome version changes often break integration tests in unpredictable ways, so we want to make any version
drift intentional. we need to run this in a separate test file to avoid async loop issues.
"""

import json

from app.configuration.versions import VERSIONS_FILE, chrome_version


def test_chrome_version_matches_persisted_version():
    persisted_chrome_version = json.loads(VERSIONS_FILE.read_bytes())["chrome"]

    assert persisted_chrome_version == chrome_version()
