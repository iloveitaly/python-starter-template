import subprocess
from importlib.metadata import version
from pathlib import Path

import pytest

from tests.playwright_chrome import use_docker_chrome

ROOT = Path(__file__).resolve().parents[2]


class _Config:
    def __init__(self, headed: bool):
        self._headed = headed

    def getoption(self, name: str) -> bool:
        assert name == "--headed"
        return self._headed


def test_compose_chrome_matches_playwright_package():
    playwright_version = version("playwright")
    compose = (ROOT / "docker-compose.yml").read_text()

    assert f"mcr.microsoft.com/playwright:v{playwright_version}-noble" in compose
    assert f"playwright@{playwright_version}" in compose
    assert "127.0.0.1:${PLAYWRIGHT_CHROME_PORT}:3000" in compose
    assert "infra/chrome-localhost-proxy.sh" in compose


def test_chrome_endpoint_uses_the_host_port():
    not_production = (ROOT / "env/not_production.sh").read_text()
    allowlist = (ROOT / ".github/actions/common-setup/action.yml").read_text()

    assert (
        "export PLAYWRIGHT_CHROME_PORT=$(( ${START_PORT} + 4 + ${PORT_OFFSET} ))"
        in not_production
    )
    assert (
        "export PLAYWRIGHT_CHROME_WS_ENDPOINT=ws://127.0.0.1:${PLAYWRIGHT_CHROME_PORT}/"
        in not_production
    )
    assert "PLAYWRIGHT_CHROME_PORT" in allowlist
    assert "PLAYWRIGHT_CHROME_WS_ENDPOINT" in allowlist


def test_localhost_proxy_decodes_default_gateway():
    # 010011AC is the little-endian gateway for 172.17.0.1, docker's usual bridge
    result = subprocess.run(
        [
            "sh",
            "infra/chrome-localhost-proxy.sh",
            "--print-host-ip",
            "010011AC",
        ],
        check=True,
        capture_output=True,
        text=True,
        cwd=ROOT,
    )

    assert result.stdout.strip() == "172.17.0.1"


def test_docker_fixtures_target_compose_chromium(
    connect_options, browser_type_launch_args, browser_context_args
):
    assert connect_options["wsEndpoint"].startswith("ws://127.0.0.1:")
    assert "--disable-quic" in browser_type_launch_args["args"]
    assert browser_type_launch_args["headless"] is True
    assert browser_context_args["ignore_https_errors"] is True
    assert browser_context_args["timezone_id"] == "UTC"
    assert browser_context_args["locale"] == "en-US"


@pytest.mark.parametrize(
    ("headed", "pwdebug", "endpoint", "expected"),
    [
        (False, None, "ws://127.0.0.1:3000/", True),
        (True, None, "ws://127.0.0.1:3000/", False),
        (False, "1", "ws://127.0.0.1:3000/", False),
        (False, "console", "ws://127.0.0.1:3000/", False),
        (False, None, None, False),
        (False, None, "", False),
    ],
)
def test_use_docker_chrome(monkeypatch, headed, pwdebug, endpoint, expected):
    monkeypatch.delenv("PWDEBUG", raising=False)
    monkeypatch.delenv("PLAYWRIGHT_CHROME_WS_ENDPOINT", raising=False)

    if pwdebug is not None:
        monkeypatch.setenv("PWDEBUG", pwdebug)

    if endpoint is not None:
        monkeypatch.setenv("PLAYWRIGHT_CHROME_WS_ENDPOINT", endpoint)

    assert use_docker_chrome(_Config(headed)) is expected
