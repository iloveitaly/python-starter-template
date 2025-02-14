"""
Utilities for helping build and tare down servers for full-stack integration tests. Some tips:

- page.pause() for a breakpoint

TODO figure out a better solution for async loops
https://github.com/microsoft/playwright-pytest/issues/74#issuecomment-2497976914

> E               playwright._impl._errors.Error: It looks like you are using Playwright Sync API inside the asyncio loop.
https://github.com/microsoft/playwright-python/issues/462
"""

import os
import time

import psutil
import pytest
import uvicorn
from decouple import config
from playwright.sync_api import Page

from app import log
from app.environments import is_local_testing
from app.server import api_app

from tests.integration.javascript_build import wait_for_javascript_build

PYTHON_SERVER_TEST_PORT = config("PYTHON_TEST_SERVER_PORT", cast=int)

_server_subprocess = None


def wait_for_termination(pid, timeout=10):
    """
    Py's multiprocessing module does not have a way to wait until a process has terminated.

    This mess is to get us that guarantee so we can terminate the server and then start another one, knowing that
    only a single dev server is running at a time.
    """

    process = psutil.Process(pid)
    process.terminate()  # Send SIGTERM

    try:
        process.wait(timeout=timeout)  # Wait for graceful shutdown
    except psutil.TimeoutExpired:
        process.kill()  # Force SIGKILL if still running
        process.wait()  # Wait for kill to complete

    # Double verify termination
    try:
        os.kill(pid, 0)  # Check if process exists
        return False
    except OSError:
        return True  # Process is confirmed dead


def wait_for_port(port: int, timeout: int = 30) -> bool:
    import socket

    from tests.conftest import log

    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                # localhost allows for ipv4 and ipv6 loopback
                sock.connect(("localhost", port))
                return True
        except ConnectionRefusedError:
            log.debug("waiting for port")
            time.sleep(0.5)

    return False


def run_server():
    """
    This method is small and dangerous.

    It runs in a fork. Depending on your system, how that process fork is constructed is different, which can lead to
    surprising behavior (like the transaction database cleaner not working). This is why we need to run
    """

    uvicorn.run(
        api_app,
        port=PYTHON_SERVER_TEST_PORT,
        # NOTE important to ensure structlog controls logging in production
        log_config=None,
        # a custom access logger is implemted which plays nicely with structlog
        access_log=False,
    )


@pytest.fixture
def server():
    """
    Spinning up the entire application for EACH TEST is extremely slow.

    However, it closely mirrors production *and* we should not have more than a few dozen integration tests. It's fine
    for these integration tests to move slowly and very closely mirror a production environment.

    https://stackoverflow.com/questions/57412825/how-to-start-a-uvicorn-fastapi-in-background-when-testing-with-pytest
    """

    from multiprocessing import Process

    # defensively code against multiprocessing coding errors
    if wait_for_port(PYTHON_SERVER_TEST_PORT, 1):
        raise Exception("server is already running, should be closed!")

    # NOTE this is a very important line! It forks an *entirely new* python process and does not inherit
    #      any state from the pytest setup. This means database sessions, redis connections, etc are entirely
    #      different in the subprocess. Do not try to inherit state from the pytest process as fork-based
    #      multiprocessing is not the default across all platforms and can introduce subtle bugs.

    proc = Process(target=run_server, args=(), daemon=True)
    proc.start()

    global _server_subprocess
    _server_subprocess = proc

    # since the server is run a daemon in another process, we need to wait until the port is ready
    if not wait_for_port(PYTHON_SERVER_TEST_PORT):
        raise Exception("server failed to start")

    wait_for_javascript_build()

    try:
        yield
    finally:
        wait_for_termination(proc.pid)

    # TODO should we install a signal trap to ensure the server is killed?


def pytest_keyboard_interrupt(excinfo):
    log.info("KeyboardInterrupt caught – stopping server...")
    if _server_subprocess:
        _server_subprocess.terminate()
    # from _pytest.config import get_config

    # config = get_config()
    # instance = getattr(config, "my_playwright_instance", None)
    # if instance is not None:
    #     print("KeyboardInterrupt caught – stopping playwright...")
    #     instance.stop()


def home_url():
    # TODO should we just use `base_server_url` instead?
    return f"https://{config('PYTHON_TEST_SERVER_HOST')}"


def wait_for_loading(page: Page):
    """
    Defensively wait for everything on the page to finish loading.

    Helpful when generating screenshots for visual comparison.
    """

    # https://stackoverflow.com/questions/71937343/playwright-how-to-wait-until-there-is-no-animation-on-the-page
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_load_state("load")
    page.wait_for_load_state("networkidle")

    # Wait for any CSS animations/transitions to complete
    # page.wait_for_function("""
    #     !Array.from(document.querySelectorAll('*')).some(
    #         element => window.getComputedStyle(element).animationName !== 'none'
    #     )
    # """)

    # some animations can still run and cause diffs
    page.wait_for_timeout(2_000)


def report_localias_status():
    """
    For integration tests, we require localalias to be running in the background since we use https.
    """
    import os
    import subprocess
    import sys

    command = ["localias", "status"]

    # on GHA we need to run localalias on sudo
    if not is_local_testing():
        command.insert(0, "sudo")

    result = subprocess.run(command, capture_output=True, text=True)
    log.debug("localias Status", output=result.stdout)

    if "daemon running" not in result.stdout:
        log.error(
            "localias daemon is not running. Integration tests may fail.",
            output=result.stdout,
        )
