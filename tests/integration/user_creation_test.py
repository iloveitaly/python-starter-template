"""
https://github.com/microsoft/playwright-pytest/issues/74#issuecomment-2497976914

> E               playwright._impl._errors.Error: It looks like you are using Playwright Sync API inside the asyncio loop.
https://github.com/microsoft/playwright-python/issues/462
"""

import time

import pytest
import uvicorn
from decouple import config
from playwright.sync_api import Page, expect

from app.models.user import User
from app.server import api_app
from tests.integration.clerk import setup_clerk_testing_token
from tests.util import get_clerk_dev_user

PYTHON_SERVER_TEST_PORT = config("PYTHON_TEST_SERVER_PORT", cast=int)


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
                log.info("server is up")
                return True
        except ConnectionRefusedError:
            log.info("waiting for port")
            time.sleep(0.5)

    log.error("Timed out waiting for port")
    return False


def run_server():
    uvicorn.run(api_app, port=PYTHON_SERVER_TEST_PORT)


@pytest.fixture
def server():
    """
    https://stackoverflow.com/questions/57412825/how-to-start-a-uvicorn-fastapi-in-background-when-testing-with-pytest
    """
    # TODO this has got to be really slow :/

    from multiprocessing import Process

    # TODO I think we should think about the forking method here; may need to reinitialize within the subprocess
    proc = Process(target=run_server, args=(), daemon=True)
    proc.start()

    # since the server is run a daemon in another process, we need to wait until the port is ready
    wait_for_port(PYTHON_SERVER_TEST_PORT)

    yield

    proc.kill()

    # TODO should we install a signal trap to ensure the server is killed?


def home_url():
    return f"https://{config("PYTHON_TEST_SERVER_HOST")}"


def test_signin(server, page: Page) -> None:
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

    assert User.count() == 1


def test_signup(server, page: Page) -> None:
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

    # https://stackoverflow.com/questions/71937343/playwright-how-to-wait-until-there-is-no-animation-on-the-page
    page.wait_for_load_state("domcontentloaded")

    # page.unroute("https://resolved-emu-53.clerk.accounts.dev/v1/**")

    # at this point the page will automatically redirect
    expect(page.locator("body")).to_contain_text("View your profile here")
    page.get_by_role("link", name="Go Home").click()

    expect(page.locator("body")).to_contain_text("Hello From Internal Python")

    # user should be created at this point!
    assert User.count() == 1

    # logout
    page.locator(".flex > div:nth-child(3)").first.click()
    page.get_by_role("menuitem", name="Sign out").click()

    expect(page.locator("body")).to_contain_text("Sign in")
