import pytest

from activemodel.pytest.truncate import database_reset_truncate

# server is imported to expose that fixture to the tests, but keep it all organized in the server file
from tests.integration.server import report_localias_status, server  # noqa: F401


def pytest_configure(config):
    report_localias_status()


# transaction truncation cannot be used with integration tests since the forked server does not retain the same
# db connection in memory and therefore the transaction rollback does not work.
database_reset_truncate = pytest.fixture(scope="function", autouse=True)(
    database_reset_truncate
)
