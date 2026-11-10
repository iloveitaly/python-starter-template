from playwright.sync_api import Page, expect

DEFAULT_LOADING_INDICATORS = (
    ".animate-spin, .loading-spinner, [aria-busy='true'], [data-loading='true']"
)


def assert_no_loading_indicators(page: Page) -> None:
    expect(page.locator(DEFAULT_LOADING_INDICATORS)).to_have_count(0)
