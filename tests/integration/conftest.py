from app import log


def report_localias_status():
    """
    For integration tests, we require localalias to be running in the background.
    """
    import subprocess

    result = subprocess.run(["localias", "status"], capture_output=True, text=True)
    log.debug("localias Status", output=result.stdout)

    if "daemon running" not in result.stdout:
        log.error(
            "localias daemon is not running. Integration tests may fail.",
            output=result.stdout,
        )


def pytest_configure(config):
    report_localias_status()
