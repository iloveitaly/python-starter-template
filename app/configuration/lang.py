"""
Using `python` for the filename would cause issues, so we use lang.

This file is meant to align python configuration options across versions to avoid
weird bugs between dev, prod, ci, etc.
"""

import multiprocessing
import os
import sys
from pathlib import Path

from app.environments import is_production


def configure_python():
    """
    Linux vs macOS changes the default spawn method, which heavily impacts how the multiprocess module operates.

    Specifically, this impacts our integration tests. They succeed on linux (fork) and not on macos (spawn)
    """
    from app import log

    inspect_python_runtime()

    if "TZ" not in os.environ:
        log.warning("TZ not set, update your environment configuration")

    try:
        # this is not the default as of py 3.13 on all platforms, but `fork` is deprecated
        if (existing_start_method := multiprocessing.get_start_method()) != "spawn":
            # if this is set multiple times, it throws an exception without force=True
            # I could not determine what is setting the start method before me here
            multiprocessing.set_start_method("spawn", force=True)

            log.info(
                "multiprocessing set to spawn", existing_method=existing_start_method
            )
        else:
            log.info("multiprocessing already set to spawn")
    except RuntimeError as e:
        log.warning(
            "multiprocessing start method failed to set",
            error=e,
            existing_method=multiprocessing.get_start_method(),
        )

    if is_production() and "PYTHONBREAKPOINT" not in os.environ and sys.breakpointhook:
        sys.breakpointhook = None
        log.info("disabling python breakpoints in production environment")


def inspect_python_runtime() -> None:
    """
    Run some runtime checks to alert on some rare-but-hard-to-debug issues.

    - Check if the Python interpreter is running in a virtual environment.
    - Check if the interpreter is the global/system Python. For instance, VSC extensions will attempt to create a
      venv with the system Python vs the mise python.

    If not, log a warning with environment details.
    """

    from app import log

    executable = Path(sys.executable).resolve()

    # is set by virtualenv (not venv) to the original prefix
    real_prefix = getattr(sys, "real_prefix", None)

    in_venv = (
        real_prefix is not None
        or sys.base_prefix != sys.prefix
        or os.environ.get("VIRTUAL_ENV") is not None
    )

    if not in_venv:
        env_var_keys = ["VIRTUAL_ENV", "PATH", "PYTHONPATH"]
        env_vars = {key: os.environ.get(key) for key in env_var_keys}

        log.warning(
            "not using a virtual environment",
            interpreter=executable,
            real_prefix=real_prefix,
            env=env_vars,
            sys_path=sys.path,
            # root directory of the current Python installation (e.g., /usr/local for system Python or /path/to/venv for virtual env)
            prefix=sys.prefix,
            # original base installation prefix (system-wide Python's prefix) in venv environments (equals sys.prefix outside venvs)
            base_prefix=sys.base_prefix,
        )
    else:
        log.debug(
            "virtual environment detected", interpreter=executable, venv=sys.prefix
        )

    # TODO there are probably other keywords we should test for
    if in_venv and ("homebrew" in str(executable) or "/usr/bin/" in str(executable)):
        log.warning(
            "using venv, but interpreter is from an unexpected location",
            interpreter=executable,
        )
