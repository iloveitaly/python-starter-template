import os
import sys

# when running locally, switching to the full-blown CI environment is a pain
# to make it quick & easy to run tests, we force the environment to test
# this will not be the same as CI, but it's closer and faster for devprod
if os.environ["PYTHON_ENV"] != "test":
    print("\033[91mPYTHON_ENV is not set to test, forcing\033[0m")
    os.environ["PYTHON_ENV"] = "test"

    assert 'app' not in sys.modules, "app modules should not be imported before environment is set"

from tests.routes.utils import MockAuthenticateRequest
import multiprocessing

from pathlib import Path
import typing as t

import pytest
from pytest import Config
from activemodel.pytest import database_reset_transaction, database_reset_truncate
from decouple import config as decouple_config
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from structlog import get_logger

# important to ensure model metadata is added to the application
import app.models  # noqa: F401

from tests.utils import delete_all_clerk_users
from tests.seeds import seed_test_data

# this file is uploaded as an artifact
TEST_RESULTS_DIRECTORY = Path(decouple_config("TEST_RESULTS_DIRECTORY", cast=str))

# TODO set logger name, not context
log = get_logger(test=True)

log.info("multiprocess start method", start_method=multiprocessing.get_start_method())

# NOTE this runs on any pytest invocation, even if no tests are run
def pytest_configure(config: Config):
    # TODO huh, maybe we should use anyio instead?
    # anyio is installed by some other packages and it's plugin is discovered automatically, we disable it in favor of asyncio
    config.option.plugins = ["no:anyio"]

    config.option.pdbcls = "pdbr:RichPdb"
    config.option.disable_warnings = True

    # playwright config
    config.option.screenshot = "only-on-failure"
    config.option.tracing = "retain-on-failure"
    # TODO although output is a generic CLI option, it's specific to playwright
    config.option.output = decouple_config("PLAYWRIGHT_RESULT_DIRECTORY", cast=str)

    # must be session to align with playwright expectations
    config.option.asyncio_mode = "auto"
    # TODO right now this option can only be set on ini, which is strange
    # config.option.asyncio_default_fixture_loop_scope = "session"

    # visual testing config
    config.option.playwright_visual_snapshot_threshold = 0.2
    config.option.playwright_visual_failure_directory = TEST_RESULTS_DIRECTORY

    # without this, if the test succeeds, no output is provided
    # this is a good default, but makes it much harder to debug what is going on
    config.option.log_cli = True
    config.option.log_cli_level = "INFO"

    # lower debug level for file debugging, so we can download this artifact and view detailed debugging
    config.option.log_file = str(TEST_RESULTS_DIRECTORY / "pytest.log")
    config.option.log_file_level = "DEBUG"


# NOTE only executes if a test is run
def pytest_sessionstart(session):
    # without this, the clerk dev instance will get cluttered and throw errors
    delete_all_clerk_users()
    # clear out any previous cruft in this DB, which is why...
    database_reset_truncate()
    # we reseed the database with a base set of records
    seed_test_data()

def base_server_url(protocol: t.Literal["http", "https"] = "http"):
    """
    VITE_PYTHON_URL is defined as the protocol + host, but the user/dev shouldn't have to worry
    about trailing slash, etc so we normalize it here.
    """

    url = decouple_config("VITE_PYTHON_URL", cast=str).strip()

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
def authenticated_client():
    "mocks out the clerk authentication and returns a static response"

    from app.server import api_app
    from app.routes.internal import authenticate_clerk_request_middleware

    api_app.dependency_overrides[authenticate_clerk_request_middleware] = MockAuthenticateRequest()

    yield TestClient(api_app, base_url=base_server_url())

    api_app.dependency_overrides = {}


@pytest.fixture
async def aclient() -> t.AsyncGenerator[AsyncClient, None]:
    from app.server import api_app

    async with AsyncClient(
        transport=ASGITransport(app=api_app),
        base_url=base_server_url(),
    ) as client:
        yield client


@pytest.fixture(scope="function", autouse=True)
def datatabase_reset_transaction_for_standard_tests(request):
    database_reset_transaction()
