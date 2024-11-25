"""
The chrome version is persisted to .chrome-version. We test to ensure the version used here matches the persisted version.

Why? Chrome version changes often break integration tests in unpredictable ways, so we want to make any version
drift intentional.
"""

from app import root


def chrome_version():
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch()
        return browser.version


def test_chrome_version_matches_persisted_version():
    assert (root / ".chrome-version").read_text().strip() == chrome_version().strip()
