import pytest

from activemodel.pytest.truncate import database_reset_truncate

# server is imported to expose that fixture to the tests, but keep it all organized in the server file
from tests.integration.javascript_build import start_js_build
from tests.integration.server import report_localias_status, server  # noqa: F401


# NOTE this runs on any pytest invocation, even if no tests are run, once per pytest invocation
def pytest_configure(config):
    # start JS build right away, since it takes some time. Separately, the test server will wait until the build
    # is finished to start running tests against the server.
    start_js_build()
    report_localias_status()


# transaction truncation cannot be used with integration tests since the forked server does not retain the same
# db connection in memory and therefore the transaction rollback does not work. To get around this, we truncate the
# database before running any tests, although this also has the side effect of destroying any test seed data.
@pytest.fixture(scope="function", autouse=True)
def truncate_database_for_integration(request):
    database_reset_truncate()
