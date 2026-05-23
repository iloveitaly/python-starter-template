"""Optional teardown pause for Playwright ``page`` fixtures (``pytest --playwright-pause``).

Overrides pytest-playwright's ``page`` by using ``context.new_page()`` so
multi-browser parametrization keeps working; see
https://github.com/microsoft/playwright-pytest/issues/172

Use ``PWDEBUG=1`` (and often ``-s``) locally so ``page.pause()`` opens the
Playwright inspector.
"""

from collections.abc import Generator

import pytest
from playwright.sync_api import BrowserContext, Page

from tests.log import log


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--playwright-pause",
        action="store_true",
        default=False,
        help="After each test using page, call page.pause() (use PWDEBUG=1 for inspector)",
    )


def _playwright_pause_enabled(config: pytest.Config) -> bool:
    return bool(getattr(config.option, "playwright_pause", False))


def pytest_configure(config: pytest.Config) -> None:
    if _playwright_pause_enabled(config):
        config.option.headed = True
        config.option.slowmo = 500


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_teardown(item: pytest.Function, nextitem: pytest.Item | None):
    """Pause before any fixture teardowns run.

    We use ``pytest_runtest_teardown`` as a hookwrapper rather than putting the
    pause inside the ``page`` fixture's post-yield block because fixture teardown
    runs in LIFO order: any fixture that depended on ``page`` (e.g. a factory or
    auth helper) tears down *before* ``page`` does.  Those fixtures often shut
    down services that the browser still needs — the local test server, database
    sessions, authentication state — making it impossible to meaningfully
    interact with the page in the inspector.

    By hooking here, the pause fires before pytest begins unwinding any fixtures,
    so the full test environment (server, DB connection, auth) remains live while
    you inspect the page.  The ``yield`` then hands control back to pytest, which
    runs all fixture teardowns normally.
    """
    if _playwright_pause_enabled(item.config) and "page" in item.funcargs:
        context: BrowserContext | None = item.funcargs.get("context")
        page: Page = item.funcargs["page"]

        if context:
            context.set_default_timeout(0)
            context.set_default_navigation_timeout(0)

        log.info("pausing playwright page", test=item.nodeid)
        page.pause()

    yield


@pytest.fixture
def page(context: BrowserContext) -> Generator[Page, None, None]:
    yield context.new_page()
