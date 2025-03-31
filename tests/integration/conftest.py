# server is imported to expose that fixture to the tests, but keep it all organized in the server file
from app import log

from tests.integration.javascript_build import start_js_build
from tests.integration.server import (  # noqa: F401
    report_localias_status,
    # IMPORTANT `server` is a fixture and this important exposes it to the tests
    server,
    terminate_server,
)


# NOTE this runs on any pytest invocation, even if no tests are run, once per pytest invocation
def pytest_configure(config):
    # start JS build right away, since it takes some time. Separately, the test server will wait until the build
    # is finished to start running tests against the server.
    start_js_build()
    report_localias_status()


def pytest_keyboard_interrupt(excinfo):
    log.info("KeyboardInterrupt caught: stopping server...")
    terminate_server()

    # Force terminate all Playwright browser processes
    # try:
    #     # Method 1: Get playwright from pytest plugin (most reliable)
    #     from pytest_playwright.pytest_playwright import playwright_fixture

    #     if "playwright" in playwright_fixture._fixtures:
    #         log.info("Stopping Playwright instances...")
    #         playwright = playwright_fixture._fixtures["playwright"]
    #         playwright.stop()
    # except Exception as e:
    #     log.warning(f"Error stopping Playwright gracefully: {e}")

    # from _pytest.config import get_config

    # config = get_config()
    # instance = getattr(config, "my_playwright_instance", None)
    # if instance is not None:
    #     print("KeyboardInterrupt caught – stopping playwright...")
    #     instance.stop()
