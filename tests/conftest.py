# ruff: disable

import os

# when running locally, switching to the full-blown CI environment is a pain
# to make it quick & easy to run tests, we force the environment to test
# this will not be the same as CI, but it's closer and faster for devprod
if os.environ["PYTHON_ENV"] != "test":
    print("\033[91mPYTHON_ENV is not set to test, forcing\033[0m")
    os.environ["PYTHON_ENV"] = "test"

import typing as t

import pytest
from activemodel.pytest import database_reset_transaction, database_reset_truncate
from decouple import config
from fastapi.testclient import TestClient
from structlog import get_logger

# important to ensure model metadata is added to the application
import app.models  # noqa: F401

# TODO set logger name, not context
log = get_logger(test=True)


# TODO this doesn't seem to fix the issue
# https://github.com/microsoft/playwright-pytest/issues/167#issuecomment-1546854047
# def pytest_configure():
#     log.info("pytest_configure: nesting asyncio loop")
#     nest_asyncio.apply()

# TODO we should look into uvloop if we end up doing async tests
# @pytest.fixture(scope="session")
# def event_loop_policy():
#     return uvloop.EventLoopPolicy()


def pytest_configure(config):
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


pytest.fixture(scope="function", autouse=True)(database_reset_transaction)
