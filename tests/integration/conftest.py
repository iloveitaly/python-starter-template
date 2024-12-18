import os

import pytest

from activemodel.pytest.truncate import database_reset_truncate

# server is imported to expose that fixture to the tests, but keep it all organized in the server file
from tests.integration.server import report_localias_status, server  # noqa: F401

if "CI" not in os.environ:
    print(
        """
\033[91m
!!! IMPORTANT !!!

You are running an integration test outside the CI=true environment.

If you are iterating on the frontend as well, your build is most likely out of date. Run:

just py_js-build
\033[0m
"""
    )


def pytest_configure(config):
    report_localias_status()


# transaction truncation cannot be used with integration tests since the forked server does not retain the same
# db connection in memory and therefore the transaction rollback does not work.
database_reset_truncate = pytest.fixture(scope="function", autouse=True)(
    database_reset_truncate
)
