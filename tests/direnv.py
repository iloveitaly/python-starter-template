"""
This is an attempt to fix a very specific problem: some tests require CI-specific environment variables.
In order to load them, and keep the state consistent across local testing and CI, we use direnv.

However, it's easier to just run `pytest` and never think about environment variables.

- This logic should only be run *locally* when running tests
"""

import glob
import hashlib
import json
import os
import subprocess
import typing as t

from .constants import TMP_DIRECTORY
from .utils import log


def is_using_direnv() -> bool:
    """
    We can't assume all developers will be using direnv locally, so let's check for the presence of
    direnv-related variables in their environment.
    """

    return "DIRENV_FILE" in os.environ


def direnv_ci_environment() -> dict[str, t.Any]:
    process_result = subprocess.run(
        # NOTE very important command! This should filter PATH, and some other stuff
        "just direnv_export_ci",
        shell=True,
        capture_output=True,
        text=True,
    )

    process_result.check_returncode()  # Raises CalledProcessError if exit code is non-zero

    raw_result = process_result.stdout

    if not raw_result.strip():
        raise ValueError("Empty output from direnv export json command")

    json_result = json.loads(raw_result)

    return json_result


def direnv_state_sha() -> str:
    # Glob all .env* files and hash their modified times
    env_files = sorted(glob.glob(".env*"))

    # make sure more than one file is found
    if len(env_files) == 0:
        raise ValueError("No .env* files found")

    mtimes = "".join(str(os.path.getmtime(f)) for f in env_files)
    sha = hashlib.sha256(mtimes.encode()).hexdigest()

    log.info("env files inspected for direnv state", env_files=env_files)

    return sha


def update_environment(env: dict[str, t.Any]) -> None:
    """
    Update the python environment in-place with the given env dict.

    Warning: This function has side effects on the current process and any subprocesses.
    Changes to environment variables like PATH, PYTHONPATH, PYTHONHOME can affect
    command resolution, module imports, and interpreter behavior.

    Args:
        env: Dictionary of environment variables to set
    """

    dangerous_keys = ["PATH", "PYTHONPATH", "PYTHONHOME"]

    for key in dangerous_keys:
        if key in env:
            raise ValueError(
                f"Attempting to modify dangerous environment variable: {key}"
            )

    for key, value in env.items():
        os.environ[key] = str(value)


def load_ci_environment():
    if not is_using_direnv():
        log.info("Skipping direnv setup, not using direnv locally")
        return

    sha = direnv_state_sha()

    direnv_state_file = TMP_DIRECTORY / f"direnv_state_{sha}"

    # if state file exists, then load the cached env state
    if direnv_state_file.exists():
        ci_environment = json.loads(direnv_state_file.read_text())
        update_environment(ci_environment)
        log.info(
            "direnv environment loaded from cache", direnv_state_file=direnv_state_file
        )

        return

    # if it doesn't exist, let's load the env state and write it to the file
    ci_environment = direnv_ci_environment()
    # compare with the current environment and only include the delta
    filtered_ci_environment = {
        k: v for k, v in ci_environment.items() if os.environ.get(k) != v
    }
    direnv_state_file.write_text(json.dumps(filtered_ci_environment))
    update_environment(filtered_ci_environment)

    log.info(
        "direnv environment loaded and cached", direnv_state_file=direnv_state_file
    )
