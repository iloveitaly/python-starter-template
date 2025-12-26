import os
import sys

import stripe

# When running locally, switching to the full-blown CI environment is a pain.
# To make it quick & easy to run tests, we force the environment to test and load cached CI environment variables (if we can).
# This will not be the same as CI, but it's closer and faster for devprod. It should never run on CI!
if os.getenv("PYTHON_ENV", "development") != "test":
    print(
        "\033[91m"
        "PYTHON_ENV is not set to 'test', forcing.\n\n"
        "Additional variables may set in 'env/test.sh' and required to run tests.\n\n"
        "Consider using `just py_test"
        "\033[0m"
    )

    os.environ["PYTHON_ENV"] = "test"

    assert "app" not in sys.modules, (
        "app modules should not be imported before environment is set"
    )

    from tests.direnv import load_ci_environment

    load_ci_environment()

import multiprocessing
from pathlib import Path

import pytest
from activemodel.pytest import database_reset_transaction, database_reset_truncate
from decouple import config as decouple_config
from pytest import Config, FixtureRequest

# important to ensure model metadata is added to the application
import app.models  # noqa: F401
from app.celery import celery_app
from app.configuration.redis import get_redis

from .constants import TEST_RESULTS_DIRECTORY
from .log import log

# add any local plugins here
# pytest_plugins = ["tests.plugins.improved_playwright_failures"]
pytest_plugins = []

log.info("multiprocess start method", start_method=multiprocessing.get_start_method())


# NOTE this runs on any pytest invocation, even if no tests are run
def pytest_configure(config: Config):
    # TODO huh, maybe we should use anyio instead?
    # TODO pretty sure this doesn't actually work to disable plugins
    # anyio is installed by some other packages and it's plugin is discovered automatically, we disable it in favor of asyncio
    config.option.plugins = ["no:anyio"]

    # when configuring in code, a tuple is used for the (mod, class) reference
    # check out _pytest/debugging.py for implementation details
    config.option.usepdb_cls = ("pdbr", "RichPdb")

    config.option.disable_warnings = True

    # this forces beautiful-traceback to be used instead of the default pytest tb, which is absolutely terrible
    config.option.tbstyle = "native"

    # playwright config
    config.option.screenshot = "only-on-failure"
    config.option.tracing = "retain-on-failure"
    # TODO although output is a generic-sounding CLI option, it's specific to playwright
    config.option.output = decouple_config("PLAYWRIGHT_RESULT_DIRECTORY", cast=str)

    # this forces pretty-traceback to be used instead of the default pytest tb, which is absolutely terrible
    config.option.tbstyle = "native"

    # must be session to align with playwright expectations
    config.option.asyncio_mode = "auto"
    # TODO right now this option can only be set on ini, which is strange
    # config.option.asyncio_default_fixture_loop_scope = "session"

    # without this, if the test succeeds, no output is provided
    # this is a good default, but makes it much harder to debug what is going on
    config.option.log_cli = True
    # config.option.log_cli_level = "INFO"

    # lower debug level for file debugging, so we can download this artifact and view detailed debugging
    config.option.log_file = str(TEST_RESULTS_DIRECTORY / "pytest.log")
    # config.option.log_file_level = "DEBUG"

    config.option.enable_beautiful_traceback = True
    config.option.enable_beautiful_traceback_local_stack_only = decouple_config(
        "BEAUTIFUL_TRACEBACK_LOCAL_ONLY", default=False, cast=bool
    )

    config.option.playwright_visual_snapshots_path = decouple_config(
        "PLAYWRIGHT_VISUAL_SNAPSHOT_DIRECTORY", cast=Path
    )
    config.option.playwright_visual_snapshot_failures_path = (
        TEST_RESULTS_DIRECTORY / "playwright_visual_snapshot_failures"
    )
    config.option.playwright_visual_snapshot_masks = [
        '[data-clerk-component="UserButton"]',
    ]

    config.option.activemodel_preserve_tables = [
        "alembic_version",
        # add any tables you want to preserve here
    ]


def pytest_sessionstart(session):
    "only executes once if a test is run, at the beginning of the test suite execution"
    from .utils import delete_all_clerk_users

    # without this, the clerk dev instance will get cluttered and throw errors
    delete_all_clerk_users()

    # clear out any previous cruft in this DB, which is why...
    database_reset_truncate(pytest_config=session.config)


@pytest.fixture(scope="function")
def sync_celery():
    """
    Include this fixture and celery tasks will run synchronously instead of in the background

    https://docs.celeryq.dev/en/stable/userguide/testing.html
    """

    # TODO I have to change the name of celery app... :/
    from app.celery import celery_app

    # celery settings to mutate
    settings = {
        "task_always_eager": True,
        "task_eager_propagates": True,
    }

    # Store original values
    original_settings = {key: celery_app.conf.get(key) for key in settings}

    # Set to sync mode
    celery_app.conf.update(settings)

    yield

    # Restore original values
    celery_app.conf.update(original_settings)


@pytest.fixture(scope="function", autouse=True)
def clear_redis():
    "clear the redis database completely before each test"
    get_redis().flushdb()
    yield


@pytest.fixture
def celery_config():
    return celery_app.conf


# TODO we should really throw an exception if integration and non-integration tests are mixed, this will cause DB related issues
def is_integration_test(request: FixtureRequest):
    integration_tests = Path(__file__).parent / "integration"

    # should never occur!
    if not integration_tests.exists():
        raise FileNotFoundError(
            f"Integration tests directory does not exist: {integration_tests}"
        )

    current_test_path = request.node.path

    # is the current test within the integration tests directory?
    if str(current_test_path).startswith(str(integration_tests)):
        return True

    return False


@pytest.fixture(scope="function", autouse=True)
def datatabase_reset_transaction_for_standard_tests(request):
    """
    Use a single entrypoint to determine what database reset strategy to use. It's important that transaction and truncation
    are not mixed, I saw very odd DB related errors when this happened.
    """

    if is_integration_test(request):
        # transaction truncation cannot be used with integration tests since the forked server does not retain the same
        # db connection in memory and therefore the transaction rollback does not work. To get around this, we truncate the
        # database before running any tests, although this also has the side effect of destroying any test seed data.
        database_reset_truncate(pytest_config=request.config)
        yield
        return

    yield from database_reset_transaction()


@pytest.fixture
def stripe_client():
    return stripe.StripeClient(decouple_config("STRIPE_SECRET_KEY"))


@pytest.fixture
def httpx_breakpoint(httpx_mock):
    """
    Debug fixture for pytest-httpx that pauses at every HTTP request interception.

    Usage:
        def test_something(httpx_breakpoint):
            # Your test code here
            # When httpx makes a request, you'll hit a breakpoint
            # and can inspect the request object

    Based on: https://til.simonwillison.net/pytest/pytest-httpx-debug
    """
    def intercept(request):
        from pprint import pprint
        import json

        print(f"\nHTTPX Request Intercepted:")
        print(f"URL: {request.url}")

        if request.content:
            try:
                print("Body:")
                pprint(json.loads(request.content))
            except (json.JSONDecodeError, TypeError):
                print(f"Body (raw): {request.content}")

        print(f"Method: {request.method}")
        print(f"Headers: {dict(request.headers)}")

        breakpoint()
        return True

    httpx_mock.should_mock = intercept
    return httpx_mock
