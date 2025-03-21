import os
import sys

# When running locally, switching to the full-blown CI environment is a pain.
# To make it quick & easy to run tests, we force the environment to test and load cached CI environment variables (if we can).
# This will not be the same as CI, but it's closer and faster for devprod. It should never run on CI!
if os.environ["PYTHON_ENV"] != "test":
    print(
        "\033[91m"
        "PYTHON_ENV is not set to 'test', forcing.\n\n"
        "Additional variables may set in '.env.test' and required to run tests.\n\n"
        "Consider using `just py_test"
        "\033[0m"
        )
    os.environ["PYTHON_ENV"] = "test"

    assert 'app' not in sys.modules, "app modules should not be imported before environment is set"

    from tests.direnv import load_ci_environment
    load_ci_environment()

# important to ensure model metadata is added to the application
import app.models  # noqa: F401

import multiprocessing

from pathlib import Path
from pretty_traceback import formatting

import pytest
from pytest import Config, FixtureRequest
from activemodel.pytest import database_reset_transaction, database_reset_truncate
from decouple import config as decouple_config

from tests.constants import TEST_RESULTS_DIRECTORY
from tests.utils import delete_all_clerk_users, log
from tests.seeds import seed_test_data

log.info("multiprocess start method", start_method=multiprocessing.get_start_method())

# TODO can we move this into pretty_traceback?
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    I hate the terrible pytest stack traces. I wanted pretty_traceback to be used instead.

    This little piece of code was hard-won:

    https://grok.com/share/bGVnYWN5_951be3b1-6811-4fda-b220-c1dd72dedc31
    """
    outcome = yield
    report = outcome.get_result()  # Get the generated TestReport object

    # Check if the report is for the 'call' phase (test execution) and if it failed
    if report.when == "call" and report.failed:
        value = call.excinfo.value
        tb = call.excinfo.tb
        formatted_traceback = formatting.exc_to_traceback_str(value, tb, color=True)
        report.longrepr = formatted_traceback


# NOTE this runs on any pytest invocation, even if no tests are run
def pytest_configure(config: Config):
    # TODO huh, maybe we should use anyio instead?
    # anyio is installed by some other packages and it's plugin is discovered automatically, we disable it in favor of asyncio
    config.option.plugins = ["no:anyio"]

    # when configuring in code, a tuple is used for the (mod, class) reference
    # check out _pytest/debugging.py for implementation details
    config.option.usepdb_cls = ('pdbr', 'RichPdb')

    config.option.disable_warnings = True

    # this forces pretty-traceback to be used instead of the default pytest tb, which is absolutely terrible
    config.option.tbstyle = "native"

    # playwright config
    config.option.screenshot = "only-on-failure"
    config.option.tracing = "retain-on-failure"
    # TODO although output is a generic CLI option, it's specific to playwright
    config.option.output = decouple_config("PLAYWRIGHT_RESULT_DIRECTORY", cast=str)

    # this forces pretty-traceback to be used instead of the default pytest tb, which is absolutely terrible
    config.option.tbstyle = "native"

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
    # config.option.log_cli_level = "INFO"

    # lower debug level for file debugging, so we can download this artifact and view detailed debugging
    config.option.log_file = str(TEST_RESULTS_DIRECTORY / "pytest.log")
    # config.option.log_file_level = "DEBUG"

    pytest.snapshot_failures_path = str( # type: ignore
        TEST_RESULTS_DIRECTORY / "playwright_visual_snapshot_failures")


def pytest_sessionstart(session):
    "only executes once if a test is run, at the beginning of the test suite execution"

    # without this, the clerk dev instance will get cluttered and throw errors
    delete_all_clerk_users()
    # clear out any previous cruft in this DB, which is why...
    database_reset_truncate()
    # we reseed the database with a base set of records
    seed_test_data()


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
        database_reset_truncate()
        yield
        return

    yield from database_reset_transaction()
