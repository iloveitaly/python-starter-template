import pytest
import uvicorn
from decouple import config
from playwright.sync_api import Page

from app.server import api_app


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
            log.info("Waiting for port %s to be available", port)
            time.sleep(0.5)
    return False


def run_server():
    uvicorn.run(api_app, port=config("PYTHON_TEST_SERVER_PORT", cast=int))


@pytest.fixture
def server():
    """
    https://stackoverflow.com/questions/57412825/how-to-start-a-uvicorn-fastapi-in-background-when-testing-with-pytest
    """
    # TODO this has got to be really slow :/

    from multiprocessing import Process

    proc = Process(target=run_server, args=(), daemon=True)
    proc.start()
    wait_for_port(config("PYTHON_TEST_SERVER_PORT", cast=int))
    yield
    proc.kill()


def test_example(server, page: Page) -> None:
    breakpoint()
    page.goto("https://web.localhost/")

    page.get_by_role("button", name="Sign up").click()
    page.get_by_label("Email address").click()
    page.get_by_label("Email address").fill("mike+clerk_test@example.com")
    page.get_by_label("Email address").press("Tab")
    page.get_by_label("Password", exact=True).fill("python-starter-template-123")
    page.get_by_role("button", name="Continue", exact=True).click()

    page.goto("https://web.localhost/")
    page.get_by_text("View your profile here").click()
    page.goto("https://web.localhost/home")
