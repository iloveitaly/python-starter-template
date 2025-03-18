# server is imported to expose that fixture to the tests, but keep it all organized in the server file
from tests.integration.javascript_build import start_js_build
from tests.integration.server import report_localias_status, server  # noqa: F401


# NOTE this runs on any pytest invocation, even if no tests are run, once per pytest invocation
def pytest_configure(config):
    # start JS build right away, since it takes some time. Separately, the test server will wait until the build
    # is finished to start running tests against the server.
    start_js_build()
    report_localias_status()
