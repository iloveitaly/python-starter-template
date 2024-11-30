"""
The chrome version is persisted to .chrome-version. We test to ensure the version used here matches the persisted version.

Why? Chrome version changes often break integration tests in unpredictable ways, so we want to make any version
drift intentional.
"""

from playwright.sync_api import Page

from app import root


def test_chrome_version_matches_persisted_version(page: Page):
    assert (
        root / ".chrome-version"
    ).read_text().strip() == page.context.browser.version.strip()
