# ruff: disable

import os

if os.environ["PYTHON_ENV"] != "test":
    print("PYTHON_ENV is not set to test, forcing")
    os.environ["PYTHON_ENV"] = "test"

import typing as t

import pytest
from activemodel import SessionManager
from decouple import config
from fastapi.testclient import TestClient
from structlog import get_logger

# important to ensure model metadata is added to the application
import app.models  # noqa: F401

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


from activemodel.pytest import truncate_db

print("huh?")


def pytest_configure(config):
    truncate_db()


# CLEANER_STRATEGY: t.Literal["truncate", "session"] = "truncate"


# if CLEANER_STRATEGY == "truncate":

#     @pytest.fixture(scope="session", autouse=True)
#     def truncate_db_tests():
#         """
#         Problem with truncation is you can't run multiple tests in parallel
#         """

#         truncate_db()

#         yield


# if CLEANER_STRATEGY == "session":


@pytest.fixture(scope="function", autouse=True)
def reset_db():
    """
    https://stackoverflow.com/questions/62433018/how-to-make-sqlalchemy-transaction-rollback-drop-tables-it-created
    https://aalvarez.me/posts/setting-up-a-sqlalchemy-and-pytest-based-test-suite/
    https://github.com/nickjj/docker-flask-example/blob/93af9f4fbf185098ffb1d120ee0693abcd77a38b/test/conftest.py#L77
    https://github.com/caiola/vinhos.com/blob/c47d0a5d7a4bf290c1b726561d1e8f5d2ac29bc8/backend/test/conftest.py#L46
    """

    engine = SessionManager.get_instance().get_engine()

    with engine.begin() as connection:
        transaction = connection.begin_nested()

        SessionManager.get_instance().session_connection = connection

        try:
            yield
        finally:
            transaction.rollback()
            connection.close()


#     print("reset_db complete")


# TODO the problem with this approach is not every connection uses the same session
# @pytest.fixture(scope="session", autouse=True)
# def reset_db():
#     start_truncation_query = """
#         BEGIN;
#         SAVEPOINT test_truncation_savepoint;
#     """

#     raw_sql_exec(start_truncation_query)

#     yield

#     end_truncation_query = """
#         ROLLBACK TO SAVEPOINT test_truncation_savepoint;
#         RELEASE SAVEPOINT test_truncation_savepoint;
#         ROLLBACK;
#     """

#     raw_sql_exec(end_truncation_query)
#     print("reset_db complete!")
