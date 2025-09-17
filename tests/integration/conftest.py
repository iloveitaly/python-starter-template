# server is imported to expose that fixture to the tests, but keep it all organized in the server file
import re
from pathlib import Path

import pytest

from app import log

from tests.integration.javascript_build import start_js_build
from tests.integration.server import (  # noqa: F401
    report_localias_status,
    # IMPORTANT `server` is a fixture and this important exposes it to the tests
    server,
    terminate_server,
)

# https://github.com/pytest-dev/pytest-asyncio/pull/871/files
pytestmark = pytest.mark.asyncio(loop_scope="package")


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """On Playwright test failure, persist the current page HTML next to other artifacts.

    We mirror pytest-playwright's per-test artifact directory (the same folder where
    screenshots and traces are stored) and write a concise `failure.html` there.
    This keeps all failure artifacts co-located for easier debugging and CI uploads.

    The built-in trace dump *does* contain this, but it's not easily readable by LLMs (or humans). By dumping the
    rendered DOM it makes it easier for LLMs to iterate on the test failure.
    """
    outcome = yield
    rep = outcome.get_result()
    if rep.when == "call" and rep.failed and "page" in item.fixturenames:
        page = item.funcargs["page"]
        output_dir = item.config.getoption("output") or "test-results"

        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        # Reconstruct pytest-playwright's per-test artifact directory by sanitizing nodeid
        # to match how screenshots/traces are organized (e.g. tests-integration-...-chromium).
        def _sanitize_for_artifacts(text: str) -> str:
            sanitized = re.sub(r"[^A-Za-z0-9]+", "-", text)
            sanitized = re.sub(r"-+", "-", sanitized).strip("-")
            return sanitized

        per_test_dir = output_path / _sanitize_for_artifacts(item.nodeid)
        per_test_dir.mkdir(parents=True, exist_ok=True)

        failure_file = per_test_dir / "failure.html"
        failure_file.write_text(page.content())

        # log for the LLMs to pick up when they analyze the output
        log.info("Wrote rendered playwright page HTML", file_path=failure_file)


# NOTE this runs on any pytest invocation, even if no tests are run, once per pytest invocation
def pytest_configure(config):
    # start JS build right away, since it takes some time. Separately, the test server will wait until the build
    # is finished to start running tests against the server.
    start_js_build()
    report_localias_status()


def pytest_keyboard_interrupt(excinfo):
    log.info("KeyboardInterrupt caught: stopping server...")
    terminate_server()

    # TODO https://grok.com/share/bGVnYWN5_e93dbbbb-0afc-46ba-b2f3-7043e1f5399e

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
