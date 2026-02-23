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

import pytest
from gitignore_parser import parse_gitignore

from app import root
from app.environments import is_local_testing

from tests.log import log

_build_done = threading.Event()
_build_process: subprocess.Popen | None = None

# Build state file, the mtime is used to trigger new js builds
BUILD_STATE_FILE = root / "tmp" / ".js_build_success"

# NOTE this line is subject to change, keep it sync with the Justfile
PYTHON_JAVASCRIPT_BUILD_CMD = ["just", "py_js-build"]


def get_latest_mtime(directory):
    "ignoring gitignore, get the latest modified time of the files in the directory"

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
    "naive function to check if the latest modified time of the web/ directory matches the last time we built the frontend"

    if not BUILD_STATE_FILE.exists():
        return False

    build_mtime = os.path.getmtime(BUILD_STATE_FILE)
    web_latest_mtime = get_latest_mtime(root / "web")
    return web_latest_mtime <= build_mtime


def wait_for_javascript_build():
    "before running an integration test, wait for the javascript build to finish"

    if not is_local_testing():
        return

    log.info("checking if javascript build has finished")

    timed_out = not _build_done.wait(timeout=60)
    if timed_out:
        raise TimeoutError("JavaScript build did not complete within timeout period")

    if _build_process is not None and _build_process.returncode != 0:
        raise RuntimeError("JavaScript build failed")

    log.info("javascript build finished successfully")


def start_js_build():
    "for integration tests, initiate a javascript build"

    if not is_local_testing():
        return

    if is_js_build_up_to_date():
        log.info("javascript build is up to date, skipping build")
        _build_done.set()
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

    log.info("starting javascript build", command=PYTHON_JAVASCRIPT_BUILD_CMD)

    global _build_process

    # run_just_recipe uses subprocess.run which blocks; we need the build to run
    # concurrently with test collection, so we use Popen + a daemon thread instead.
    _build_process = subprocess.Popen(
        PYTHON_JAVASCRIPT_BUILD_CMD,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    def monitor_javascript_build():
        assert _build_process
        stdout, stderr = _build_process.communicate()

        if _build_process.returncode != 0:
            log.error(
                "javascript build failed",
                stdout=stdout,
                stderr=stderr,
            )
            _build_done.set()
            pytest.exit("JavaScript build failed")
        else:
            log.info("javascript build finished")
            BUILD_STATE_FILE.touch()
            _build_done.set()

    # spin up a separate thread to monitor the build process
    threading.Thread(target=monitor_javascript_build, daemon=True).start()
