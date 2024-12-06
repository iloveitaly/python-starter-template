import pytest
from activemodel.pytest.truncate import database_reset_truncate
from app import log


def report_localias_status():
    """
    For integration tests, we require localalias to be running in the background since we use https.
    """
    import os
    import subprocess
    import sys

    command = ["localias", "status"]

    # on CI we need to run localalias on sudo
    if os.getenv("CI") and sys.platform != "darwin":
        command.insert(0, "sudo")

    result = subprocess.run(command, capture_output=True, text=True)
    log.debug("localias Status", output=result.stdout)

    if "daemon running" not in result.stdout:
        log.error(
            "localias daemon is not running. Integration tests may fail.",
            output=result.stdout,
        )


def pytest_configure(config):
    report_localias_status()


database_reset_truncate = pytest.fixture(scope="function", autouse=True)(
    database_reset_truncate
)
