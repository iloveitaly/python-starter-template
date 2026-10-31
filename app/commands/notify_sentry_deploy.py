"""
Record a Sentry deploy for the release that just went live.

Dokku runs `perform` from `scripts.dokku.postdeploy` once per deploy, after the new containers pass healthchecks. Container restarts do not run that hook.

A Sentry outage must not fail the deploy. `postdeploy` runs after traffic has moved, and a non-zero exit fails `git:from-image`. A missing release version or auth config still raises.
"""

from urllib.parse import quote

import httpx2
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_none

from app import log
from app.constants import BUILD_COMMIT
from app.env import env
from app.environments import python_environment

SENTRY_API_BASE_URL = "https://sentry.io/api/0"
SENTRY_DEPLOY_ATTEMPTS = 3
SENTRY_DEPLOY_TIMEOUT_SECONDS = 10


class SentryUnreachable(Exception):
    "Sentry did not answer the deploy notification. Retried, then ignored."


class SentryDeployRejected(Exception):
    "Sentry refused the deploy notification. Not retried."

    def __init__(self, status_code: int, body: str):
        self.status_code = status_code
        self.body = body
        super().__init__(
            f"sentry deploy notification rejected with status {status_code}"
        )


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
) -> bool:
    "POST a deploy for an existing Sentry release. Outages are logged and swallowed."

    if not version or version == "dev":
        raise ValueError("BUILD_COMMIT is required to notify Sentry of a deploy")

    if not organization or not token:
        raise ValueError(
            "SENTRY_ORG and SENTRY_AUTH_TOKEN are required to notify Sentry of a deploy"
        )

    try:
        _post_deploy(
            url=_deploy_url(organization, version),
            token=token,
            environment=environment,
        )
    except SentryUnreachable:
        log.warning(
            "sentry deploy notification skipped",
            version=version,
            environment=environment,
            attempts=SENTRY_DEPLOY_ATTEMPTS,
        )
        return False
    except SentryDeployRejected as exc:
        log.error(
            "sentry deploy notification rejected",
            status_code=exc.status_code,
            body=exc.body,
            version=version,
            environment=environment,
        )
        return False

    log.info(
        "sentry deploy created",
        version=version,
        environment=environment,
    )
    return True


def _deploy_url(organization: str, version: str) -> str:
    org = quote(organization, safe="")
    release = quote(version, safe="")
    return f"{SENTRY_API_BASE_URL}/organizations/{org}/releases/{release}/deploys/"


@retry(
    retry=retry_if_exception_type(SentryUnreachable),
    stop=stop_after_attempt(SENTRY_DEPLOY_ATTEMPTS),
    wait=wait_none(),
    reraise=True,
)
def _post_deploy(url: str, token: str, environment: str) -> None:
    try:
        response = httpx2.post(
            url,
            json={"environment": environment},
            headers={"Authorization": f"Bearer {token}"},
            timeout=SENTRY_DEPLOY_TIMEOUT_SECONDS,
        )
    except httpx2.HTTPError as exc:
        raise SentryUnreachable("sentry deploy notification unreachable") from exc

    if response.status_code == 429 or response.status_code >= 500:
        raise SentryUnreachable(
            f"sentry deploy notification failed with status {response.status_code}"
        )

    if response.status_code >= 400:
        raise SentryDeployRejected(response.status_code, response.text[:500])
