import json

import httpx2
import pytest

from app.commands.notify_sentry_deploy import notify_sentry_deploy


def test_notify_sentry_deploy_posts_release_deploy(httpx2_mock):
    httpx2_mock.add_response(status_code=201, json={"id": "1"})

    created = notify_sentry_deploy(
        organization="acme",
        token="token",
        version="abc123",
        environment="production",
    )

    assert created is True
    request = httpx2_mock.get_requests()[0]
    assert request.method == "POST"
    assert request.url.path == "/api/0/organizations/acme/releases/abc123/deploys/"
    assert request.headers["authorization"] == "Bearer token"
    assert json.loads(request.content) == {"environment": "production"}


def test_notify_sentry_deploy_retries_server_errors(httpx2_mock):
    httpx2_mock.add_response(status_code=503)
    httpx2_mock.add_response(status_code=503)
    httpx2_mock.add_response(status_code=201, json={})

    created = notify_sentry_deploy(
        organization="acme",
        token="token",
        version="abc123",
        environment="staging",
    )

    assert created is True
    assert len(httpx2_mock.get_requests()) == 3


def test_notify_sentry_deploy_skips_when_sentry_is_unreachable(httpx2_mock):
    httpx2_mock.add_exception(httpx2.TimeoutException("timed out"))
    httpx2_mock.add_exception(httpx2.TimeoutException("timed out"))
    httpx2_mock.add_exception(httpx2.TimeoutException("timed out"))

    created = notify_sentry_deploy(
        organization="acme",
        token="token",
        version="abc123",
        environment="production",
    )

    assert created is False
    assert len(httpx2_mock.get_requests()) == 3


def test_notify_sentry_deploy_does_not_retry_client_errors(httpx2_mock):
    httpx2_mock.add_response(status_code=400, text="unknown release")

    created = notify_sentry_deploy(
        organization="acme",
        token="token",
        version="abc123",
        environment="production",
    )

    assert created is False
    assert len(httpx2_mock.get_requests()) == 1


def test_notify_sentry_deploy_requires_a_release_version():
    with pytest.raises(ValueError, match="BUILD_COMMIT"):
        notify_sentry_deploy(
            organization="acme",
            token="token",
            version="dev",
            environment="production",
        )


def test_notify_sentry_deploy_requires_auth():
    with pytest.raises(ValueError, match="SENTRY_AUTH_TOKEN"):
        notify_sentry_deploy(
            organization="acme",
            token="",
            version="abc123",
            environment="production",
        )
