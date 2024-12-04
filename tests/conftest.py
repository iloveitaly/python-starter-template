import multiprocessing
import os

# when running locally, switching to the full-blown CI environment is a pain
# to make it quick & easy to run tests, we force the environment to test
# this will not be the same as CI, but it's closer and faster for devprod
if os.environ["PYTHON_ENV"] != "test":
    print("\033[91mPYTHON_ENV is not set to test, forcing\033[0m")
    os.environ["PYTHON_ENV"] = "test"

# this is not the default as of py 3.13 on all platforms, but `fork` is deprecated
# if this is set multiple times, it throws an exception
# if multiprocessing.get_start_method() != "spawn":
    # if this is set multiple times, it throws an exception
multiprocessing.set_start_method("spawn")

import typing as t

import pytest
from activemodel.pytest import database_reset_transaction, database_reset_truncate
from decouple import config
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from structlog import get_logger

# important to ensure model metadata is added to the application
import app.models  # noqa: F401
from tests.utils import delete_all_users

# TODO set logger name, not context
log = get_logger(test=True)

log.info("multiprocess start method", start_method=multiprocessing.get_start_method())


# NOTE this runs on any pytest invocation, even if no tests are run
def pytest_configure(config):
    pass


# NOTE only executes if a test is run
def pytest_sessionstart(session):
    delete_all_users()
    database_reset_truncate()


def base_server_url(protocol: t.Literal["http", "https"] = "http"):
    """
    VITE_PYTHON_URL is defined as the protocol + host, but the user shouldn't have to worry
    about trailing slash, etc so we normalize it here.
    """

    url = config("VITE_PYTHON_URL", cast=str).strip()

    # Remove any existing protocol
    if url.startswith(("http://", "https://")):
        url = url.split("://")[1]

    # Remove any trailing slashes
    url = url.rstrip("/")

    # Add protocol and trailing slash
    return f"{protocol}://{url}/"


@pytest.fixture
def client():
    from app.server import api_app

    return TestClient(api_app, base_url=base_server_url())


@pytest.fixture
async def aclient() -> t.AsyncGenerator[AsyncClient, None]:
    from app.server import api_app

    async with AsyncClient(
        transport=ASGITransport(app=api_app),
        base_url=base_server_url(),
    ) as client:
        yield client


database_reset_transaction = pytest.fixture(scope="function", autouse=True)(
    database_reset_transaction
)
