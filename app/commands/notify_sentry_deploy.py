"""
Record a Sentry deploy for the release that just went live.

Dokku runs `perform` from `scripts.dokku.postdeploy` once per deploy, after the new containers pass healthchecks. Container restarts do not run that hook.

The command shells out to `sentry-cli`, which mise installs into the runtime image. A Sentry outage must not fail the deploy: `postdeploy` runs after traffic has moved, and a non-zero exit fails `git:from-image`. A missing release version or auth config still raises.
"""

import os
import subprocess
from collections.abc import Callable

from app import log
from app.constants import BUILD_COMMIT
from app.env import env
from app.environments import python_environment

SENTRY_CLI_TIMEOUT_SECONDS = 60


def perform() -> None:
    "Record the running release as a Sentry deploy for this environment."

    notify_sentry_deploy(
        organization=env.str("SENTRY_ORG"),
        token=env.str("SENTRY_AUTH_TOKEN"),
        version=BUILD_COMMIT,
        environment=python_environment().value,
    )


def notify_sentry_deploy(
    organization: str,
    token: str,
    version: str,
    environment: str,
    *,
    run: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> bool:
    "Run `sentry-cli deploys new`. Outages are logged and swallowed."

    if not version or version == "dev":
        raise ValueError("BUILD_COMMIT is required to notify Sentry of a deploy")

    if not organization or not token:
        raise ValueError(
            "SENTRY_ORG and SENTRY_AUTH_TOKEN are required to notify Sentry of a deploy"
        )

    command_env = os.environ.copy()
    command_env["SENTRY_AUTH_TOKEN"] = token
    command_env["SENTRY_ORG"] = organization

    try:
        completed = run(
            [
                "sentry-cli",
                "deploys",
                "new",
                "--org",
                organization,
                "--release",
                version,
                "--env",
                environment,
            ],
            env=command_env,
            capture_output=True,
            text=True,
            timeout=SENTRY_CLI_TIMEOUT_SECONDS,
            check=False,
        )
    except subprocess.TimeoutExpired:
        log.warning(
            "sentry deploy notification skipped",
            version=version,
            environment=environment,
            timeout=SENTRY_CLI_TIMEOUT_SECONDS,
        )
        return False

    if completed.returncode != 0:
        log.error(
            "sentry deploy notification failed",
            version=version,
            environment=environment,
            returncode=completed.returncode,
            stderr=(completed.stderr or "")[:500],
        )
        return False

    log.info(
        "sentry deploy created",
        version=version,
        environment=environment,
    )
    return True
