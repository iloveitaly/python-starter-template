"""
Utilities for helping build and tare down servers for full-stack integration tests. Some tips:

TODO figure out a better solution for async loops
https://github.com/microsoft/playwright-pytest/issues/74#issuecomment-2497976914

> E               playwright._impl._errors.Error: It looks like you are using Playwright Sync API inside the asyncio loop.
https://github.com/microsoft/playwright-python/issues/462
"""

import os
import time

import psutil
import pytest
import uvicorn
from decouple import config
from furl import furl

from app import log
from app.environments import is_local_testing
from app.server import api_app
from app.utils.debug import install_remote_debugger

from tests.constants import PYTHON_TEST_SERVER_HOST
from tests.integration.javascript_build import wait_for_javascript_build

PYTHON_SERVER_TEST_PORT = config("PYTHON_TEST_SERVER_PORT", cast=int)

_server_subprocess = None


def terminate_server():
    global _server_subprocess
    if _server_subprocess:
        _server_subprocess.terminate()


def wait_for_termination(pid, timeout=10) -> bool:
    """
    Py's multiprocessing module does not have a way to wait until a process has terminated.

    This mess is to guarantee the old server is terminated and then start another one, knowing that
    only a single dev server is running at a time.

    Returns true if process was successfully killed
    """

    process = psutil.Process(pid)
    process.terminate()  # Send SIGTERM

    try:
        process.wait(timeout=timeout)  # Wait for graceful shutdown
    except psutil.TimeoutExpired:
        log.warning("process did not terminate in time, sending SIGKILL")
        process.kill()  # Force SIGKILL if still running
        process.wait()  # Wait for kill to complete

    # Double verify termination
    try:
        # 0 is special signal which checks if process with pid exists
        os.kill(pid, 0)
        log.warning("after aggressive kill, process is still alive")
        return False
    except OSError:
        return True  # Process is confirmed dead


def wait_for_port(port: int, timeout: int = 30) -> bool:
    import socket

    from tests.conftest import log

    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                # localhost allows for ipv4 and ipv6 loopback
                sock.connect(("localhost", port))
                return True
        except ConnectionRefusedError:
            log.debug("waiting for port")
            time.sleep(0.5)

    return False


def run_server():
    """
    This method is small and dangerous.

    It runs in a fork. Depending on your system, how that process fork is constructed is different, which can lead to
    surprising behavior (like the transaction database cleaner not working). This is why we need to run
    """

    # the server does NOT have access to stdin, so let's use a piped debugging server
    install_remote_debugger()

    # TODO we should be able to assert code signature on configuration in `main.py` so this alerts us when we are out of sync

    uvicorn.run(
        api_app,
        port=PYTHON_SERVER_TEST_PORT,
        # NOTE important to ensure structlog controls logging in production
        log_config=None,
        # a custom access logger is implemted which plays nicely with structlog
        access_log=False,
        # paranoid settings!
        reload=False,
    )


@pytest.fixture
def server():
    """
    Spinning up the entire application for EACH TEST is extremely slow.

    However, it closely mirrors production *and* we should not have more than a few dozen integration tests. It's fine
    for these integration tests to move slowly and very closely mirror a production environment.

    https://stackoverflow.com/questions/57412825/how-to-start-a-uvicorn-fastapi-in-background-when-testing-with-pytest
    """

    from multiprocessing import Process

    # defensively code against multiprocessing coding errors
    if wait_for_port(PYTHON_SERVER_TEST_PORT, 1):
        raise Exception(
            "server is already running, should be closed! Use `just dev_kill` to terminall all processes holding ports."
        )

    # NOTE this is a very important line! It forks an *entirely new* python process and does not inherit
    #      any state from the pytest setup. This means database sessions, redis connections, etc are entirely
    #      different in the subprocess. Do not try to inherit state from the pytest process as fork-based
    #      multiprocessing is not the default across all platforms and can introduce subtle bugs.

    proc = Process(target=run_server, args=(), daemon=True)
    proc.start()

    global _server_subprocess
    _server_subprocess = proc

    # since the server is run a daemon in another process, we need to wait until the port is ready
    if not wait_for_port(PYTHON_SERVER_TEST_PORT):
        raise Exception("server failed to start")

    try:
        wait_for_javascript_build()

        yield
    finally:
        assert wait_for_termination(proc.pid)

    # TODO should we install a signal trap to ensure the server is killed?


def home_url():
    # TODO should we just use `base_server_url` instead?
    return str(furl(scheme="https", host=PYTHON_TEST_SERVER_HOST))


def report_localias_status():
    """
    For integration tests, we require localalias to be running in the background since we use https.

    TODO https://github.com/peterldowns/localias/issues/64
    """
    import subprocess

    command = ["localias", "status"]

    # on GHA we need to run localalias on sudo
    if not is_local_testing():
        command.insert(0, "sudo")

    result = subprocess.run(command, capture_output=True, text=True)
    log.debug("localias Status", output=result.stdout)

    if "daemon running" not in result.stdout:
        log.error(
            "localias daemon is not running. Integration tests may fail.",
            output=result.stdout,
        )
