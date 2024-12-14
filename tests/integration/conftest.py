import pytest

from activemodel.pytest.truncate import database_reset_truncate

from tests.integration.server import report_localias_status, server


def pytest_configure(config):
    report_localias_status()


database_reset_truncate = pytest.fixture(scope="function", autouse=True)(
    database_reset_truncate
)
