"""
Integration tests are designed to run in an environment that closely mirrors production.

Part of this means it uses production-build javascript assets. Ideally, these are always built
*before* running the integration tests, but it's very easy to forget to do this when iterating on tests.

In CI, the javascript assets are built before running any tests. Locally, we assume that you forgot
and automatically kick off a build for you.
"""

import subprocess
import threading
import time

from app.environments import is_local_testing

from tests.utils import log

js_build_success = None


def wait_for_javascript_build():
    "before running an integration test, wait for the javascript build to finish"

    if not is_local_testing():
        return

    if js_build_success is None:
        raise RuntimeError("JavaScript build has not been started")

    log.info("Checking if JavaScript build has finished...")

    # arbitrary timeout of 1 minute, may need to adjust as build becomes more complex
    timeout = 60 * 1
    start = time.time()

    while not js_build_success:
        if time.time() - start > timeout:
            raise TimeoutError(
                "JavaScript build did not complete within timeout period"
            )

        log.info("Waiting for JavaScript build to finish...")
        time.sleep(1)


def start_js_build():
    "for integration tests, initiate a javascript build"

    if not is_local_testing():
        return

    print(
        """
\033[91m
!!! IMPORTANT !!!

You are running an integration test outside the CI=true environment.

If you are iterating on the frontend as well, your build is most likely out of date.
A new Javascript build has been automatically kicked off for you. To run one manually, execute:

$ just py_js-build

\033[0m
"""
    )

    global js_build_success
    js_build_success = False

    log.info("Starting Javascript Build...")

    build_process = subprocess.Popen(
        # NOTE this line is subjet to change, keep it sync with the Justfile
        ["just", "py_js-build"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    def monitor_javascript_build():
        global js_build_success
        stdout, stderr = build_process.communicate()

        if build_process.returncode != 0:
            log.error(
                "Javascript build failed:\nSTDOUT:\n%s\n\nSTDERR:\n%s", stdout, stderr
            )
            js_build_success = False
        else:
            log.info("Javascript Build finished")
            js_build_success = True

    # spin up a separate thread to monitor the build process
    threading.Thread(target=monitor_javascript_build, daemon=True).start()
