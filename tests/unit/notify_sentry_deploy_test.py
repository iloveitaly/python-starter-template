import subprocess

import pytest

from app.commands.notify_sentry_deploy import notify_sentry_deploy


def _completed(returncode: int, stderr: str = "") -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(
        args=[],
        returncode=returncode,
        stdout="",
        stderr=stderr,
    )


def test_notify_sentry_deploy_runs_sentry_cli():
    calls = []

    def run(args, **kwargs):
        calls.append((args, kwargs))
        return _completed(0)

    created = notify_sentry_deploy(
        organization="acme",
        token="token",
        version="abc123",
        environment="production",
        run=run,
    )

    assert created is True
    args, kwargs = calls[0]
    assert args == [
        "sentry-cli",
        "deploys",
        "new",
        "--org",
        "acme",
        "--release",
        "abc123",
        "--env",
        "production",
    ]
    assert kwargs["env"]["SENTRY_AUTH_TOKEN"] == "token"
    assert kwargs["env"]["SENTRY_ORG"] == "acme"
    assert kwargs["check"] is False


def test_notify_sentry_deploy_skips_when_the_cli_fails():
    def run(args, **kwargs):
        return _completed(1, stderr="unauthorized")

    created = notify_sentry_deploy(
        organization="acme",
        token="token",
        version="abc123",
        environment="production",
        run=run,
    )

    assert created is False


def test_notify_sentry_deploy_skips_when_the_cli_times_out():
    def run(args, **kwargs):
        raise subprocess.TimeoutExpired(cmd=args, timeout=kwargs["timeout"])

    created = notify_sentry_deploy(
        organization="acme",
        token="token",
        version="abc123",
        environment="staging",
        run=run,
    )

    assert created is False


def test_notify_sentry_deploy_requires_a_release_version():
    def run(args, **kwargs):
        raise AssertionError("sentry-cli should not run")

    with pytest.raises(ValueError, match="BUILD_COMMIT"):
        notify_sentry_deploy(
            organization="acme",
            token="token",
            version="dev",
            environment="production",
            run=run,
        )


def test_notify_sentry_deploy_requires_auth():
    def run(args, **kwargs):
        raise AssertionError("sentry-cli should not run")

    with pytest.raises(ValueError, match="SENTRY_AUTH_TOKEN"):
        notify_sentry_deploy(
            organization="acme",
            token="",
            version="abc123",
            environment="production",
            run=run,
        )


def test_sentry_cli_deploys_command_is_installed():
    completed = subprocess.run(
        ["sentry-cli", "deploys", "new", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0
    assert "--release" in completed.stdout
    assert "--env" in completed.stdout
