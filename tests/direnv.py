import glob
import hashlib
import json
import os
import subprocess
import typing as t

from tests.constants import TEST_RESULTS_DIRECTORY, TMP_DIRECTORY

from .utils import log


def direnv_ci_environment() -> dict[str, t.Any]:
    # Execute command and capture output
    process_result = subprocess.run(
        # TODO should just instead
        "CI=true direnv exec ~ direnv export json",
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
    sha = direnv_state_sha()

    direnv_state_file = TMP_DIRECTORY / f"direnv_state_{sha}"

    # if state file exists, then load the cached env state
    if direnv_state_file.exists():
        ci_environment = json.loads(direnv_state_file.read_text())
        update_environment(ci_environment)
        return

    # if it doesn't exist, let's load the env state and write it to the file
    ci_environment = direnv_ci_environment()
    direnv_state_file.write_text(json.dumps(ci_environment))
    update_environment(ci_environment)
    return

    # if it doesn't exist, let's load the env state and write it to the file
