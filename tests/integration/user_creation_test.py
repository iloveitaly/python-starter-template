"""
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
from playwright.sync_api import Page, expect

from app.models.user import User
from app.server import api_app
from tests.integration.clerk import setup_clerk_testing_token
from tests.utils import get_clerk_dev_user

PYTHON_SERVER_TEST_PORT = config("PYTHON_TEST_SERVER_PORT", cast=int)


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
    import time

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

    uvicorn.run(api_app, port=PYTHON_SERVER_TEST_PORT)


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

    # since the server is run a daemon in another process, we need to wait until the port is ready
    if not wait_for_port(PYTHON_SERVER_TEST_PORT):
        raise Exception("server failed to start")

    try:
        yield
    finally:
        wait_for_termination(proc.pid)

    # TODO should we install a signal trap to ensure the server is killed?


def home_url():
    # TODO should we just use `base_server_url` instead?
    return f"https://{config("PYTHON_TEST_SERVER_HOST")}"


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


def test_signin(server, page: Page, assert_snapshot) -> None:
    username, password, user = get_clerk_dev_user()

    # paranoid testing to ensure database cleaning is working
    assert User.count() == 0

    setup_clerk_testing_token(page)

    page.goto(home_url())

    page.get_by_label("Email address").fill(username)
    page.get_by_role("button", name="Continue", exact=True).click()

    page.get_by_label("Password", exact=True).fill(password)
    page.get_by_role("button", name="Continue").click()

    expect(page.locator("body")).to_contain_text("Hello From Internal Python")

    assert_snapshot(page)

    assert User.count() == 1


def test_signup(server, page: Page, assert_snapshot) -> None:
    # paranoid testing to ensure database cleaning is working
    assert User.count() == 0

    setup_clerk_testing_token(page)

    unix_timestamp = int(time.time())

    page.goto(home_url())

    page.get_by_text("Sign up").click()

    page.get_by_label("Email address").click()
    page.get_by_label("Email address").fill(
        f"mike-{unix_timestamp}+clerk_test@example.com"
    )
    page.get_by_label("Password", exact=True).fill("python-starter-template-123")
    page.get_by_role("button", name="Continue", exact=True).click()

    # wait_for_timeout is milliseconds

    page.get_by_label("Enter verification code. Digit").fill("4")
    page.wait_for_timeout(100)
    page.get_by_label("Digit 2").fill("2")
    page.wait_for_timeout(100)
    page.get_by_label("Digit 3").fill("4")
    page.wait_for_timeout(100)
    page.get_by_label("Digit 4").fill("2")
    page.wait_for_timeout(100)
    page.get_by_label("Digit 5").fill("4")
    page.wait_for_timeout(100)
    page.get_by_label("Digit 6").fill("2")

    wait_for_loading(page)

    # page.unroute("https://resolved-emu-53.clerk.accounts.dev/v1/**")

    # at this point the page will automatically redirect
    expect(page.locator("body")).to_contain_text("View your profile here")
    page.get_by_role("link", name="Go Home").click()

    wait_for_loading(page)

    # assert_snapshot(page)

    expect(page.locator("body")).to_contain_text("Hello From Internal Python")

    wait_for_loading(page)

    # assert_snapshot(page)

    # user should be created at this point!
    assert User.count() == 1

    # logout
    page.locator(".flex > div:nth-child(3)").first.click()
    page.get_by_role("menuitem", name="Sign out").click()

    expect(page.locator("body")).to_contain_text("Sign in")
