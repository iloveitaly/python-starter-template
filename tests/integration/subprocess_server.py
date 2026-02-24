"""
Clean entrypoint for the integration test server subprocess.

WHY THIS FILE EXISTS
--------------------
Integration tests use `multiprocessing` with the `spawn` start method. When the child
process is spawned, Python re-imports the target module from scratch. If `run_server`
lived in `server.py`, the child would import `server.py`, which has top-level `app.*`
imports. Those imports trigger `app/__init__.py -> setup()`, which configures structlog
and emits log lines — *before* `configure_subprocess_capture()` has a chance to redirect
stdout/stderr into the per-test artifact files. The result is server startup logs leaking
to the terminal instead of being captured.

By isolating `run_server` here, the child process only imports this file. All `app.*`
imports are intentionally deferred to inside `run_server()` so that
`configure_subprocess_capture()` runs first and captures everything.

RULES FOR FUTURE DEVELOPERS
----------------------------
1. Keep ALL `app.*` imports inside `run_server()` — never at module level.
2. `configure_subprocess_capture()` must remain the very first call in `run_server()`.
3. Do not add fixture helpers, pytest imports, or test utilities to this file. It must
   stay a minimal, stdlib/third-party-only module at the top level.
4. If you add server configuration logic that belongs here, verify the hash check below
   still reflects `main.get_server_config` and update the expected hash accordingly.
"""

import os

import uvicorn
from structlog_config.pytest_plugin import configure_subprocess_capture


def run_server():
    """
    This method is small and dangerous.

    It runs in a fork. Depending on your system, how that process fork is constructed is different, which can lead to
    surprising behavior (like the transaction database cleaner not working). This is why we need to run
    """

    # this MUST be run first, even the remote debugging installation will trigger app/__init__ to run and output logs
    configure_subprocess_capture()

    import main
    from app.env import env
    from app.server import api_app
    from app.utils.debug import install_remote_debugger
    from app.utils.patching import hash_function_code

    # set a environment variable to indicate that we are running this server for integration tests
    os.environ["PYTEST_INTEGRATION_TESTING"] = "true"

    # the server does NOT have access to stdin, so let's use a piped debugging server
    install_remote_debugger()

    # NOTE: if this hash changes, it means the server configuration in `main.py` has changed
    #       and we should verify that this file also needs to be updated.
    actual_hash = hash_function_code(main.get_server_config)
    expected_hash = "a5bd757d26473d74a6381571e99d9ccf39873311c11d4b54bf7669143609d4ce"
    assert actual_hash == expected_hash, (
        f"main.py config has changed. New hash: {actual_hash}"
    )

    uvicorn.run(
        api_app,
        port=env.int("PYTHON_TEST_SERVER_PORT"),
        # NOTE important to ensure structlog controls logging in production
        log_config=None,
        # a custom access logger is implemented which plays nicely with structlog
        access_log=False,
        # paranoid settings!
        reload=False,
    )
