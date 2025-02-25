"""
Integration tests are designed to run in an environment that closely mirrors production.

Part of this means it uses production-build javascript assets. Ideally, these are always built
*before* running the integration tests, but it's very easy to forget to do this when iterating on tests.

We are doing some extra-fancy stuff here by calculating the more recent mtime of the files in web/
and using that to determine if a new build should be kicked off. We will regret this at some point.

In CI, the javascript assets are built before running any tests. Locally, we assume that you forgot
and automatically kick off a build for you.
"""

import os
import subprocess
import threading
import time

from gitignore_parser import parse_gitignore

from app import root
from app.environments import is_local_testing

from tests.utils import log

js_build_success = None

# Build state file, the mtime is used to trigger new js builds
BUILD_STATE_FILE = root / "tmp" / ".js_build_success"


def get_latest_mtime(directory):
    matches = parse_gitignore(directory / ".gitignore")

    latest = 0
    inspected_files = []

    for root_dir, dirs, files in os.walk(directory):
        if matches(root_dir):
            dirs[:] = []
            continue

        for file in files:
            file_path = os.path.join(root_dir, file)

            if not matches(file_path):
                latest = max(latest, os.path.getmtime(file_path))
                inspected_files.append(file_path)

    log.debug(
        "files checked for javascript build",
        inspected_files=inspected_files,
    )
    return latest


def is_js_build_up_to_date():
    if not BUILD_STATE_FILE.exists():
        return False
    build_mtime = os.path.getmtime(BUILD_STATE_FILE)
    web_latest_mtime = get_latest_mtime(root / "web")
    return web_latest_mtime <= build_mtime


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

    log.info("JavaScript build finished successfully")


def start_js_build():
    "for integration tests, initiate a javascript build"

    if not is_local_testing():
        return

    global js_build_success

    if is_js_build_up_to_date():
        log.info("JavaScript build is up to date. Skipping build.")
        js_build_success = True
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
            BUILD_STATE_FILE.touch()  # Update build state on success
            js_build_success = True

    # spin up a separate thread to monitor the build process
    threading.Thread(target=monitor_javascript_build, daemon=True).start()
