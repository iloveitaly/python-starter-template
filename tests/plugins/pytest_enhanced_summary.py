# pytest_enhanced_summary.py

import pytest


@pytest.hookimpl
def pytest_terminal_summary(terminalreporter, exitstatus, config):
    failed = terminalreporter.stats.get("failed", [])
    if failed:
        terminalreporter.section("Enhanced Failure Summary", sep="-", bold=True)
        for rep in failed:
            nodeid = rep.nodeid
            if hasattr(rep.longrepr, "reprcrash"):
                fail_file = rep.longrepr.reprcrash.path
                fail_line = rep.longrepr.reprcrash.lineno
                message = rep.longrepr.reprcrash.message
            else:
                fail_file = rep.location[0]
                fail_line = rep.location[1]
                message = rep.longreprtext.splitlines()[-1]

            terminalreporter.write_line(
                f"{nodeid} failed at {fail_file}:{fail_line} - {message}"
            )
