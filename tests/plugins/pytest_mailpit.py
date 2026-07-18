from collections.abc import Iterator
from urllib.parse import urlparse

import httpx2
import pytest

from app.configuration.emailer import SMTP_URL


def default_mailpit_api_url() -> str:
    smtp_url = urlparse(SMTP_URL)
    hostname = smtp_url.hostname

    if not hostname:
        raise ValueError("SMTP_URL must include a hostname for Mailpit tests")

    return f"http://{hostname}:8025/api/v1"


class MailpitClient:
    """
    Small sync client for Mailpit's HTTP API used by tests.

    TODO: This latest-message flow assumes tests are not running in parallel against
    a shared Mailpit instance. If parallelism is enabled, switch to a unique
    per-test marker and search/filter by that marker instead of clearing the
    global inbox and reading the latest message.
    """

    def __init__(self, base_url: str | None = None):
        self._client = httpx2.Client(base_url=base_url or default_mailpit_api_url())

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()

    def close(self) -> None:
        self._client.close()

    def delete_all_messages(self) -> None:
        response = self._client.delete("/messages")
        response.raise_for_status()

    def list_messages(self, *, limit: int = 50) -> list[dict]:
        response = self._client.get("/messages", params={"limit": limit})
        response.raise_for_status()
        return response.json()["messages"]

    def get_message(self, message_id: str) -> dict:
        response = self._client.get(f"/message/{message_id}")
        response.raise_for_status()
        return response.json()

    def only_last_message(self) -> dict:
        messages = self.list_messages(limit=2)
        assert len(messages) == 1, (
            f"Expected exactly one Mailpit message, found {len(messages)}"
        )
        return self.get_message(messages[0]["ID"])


@pytest.fixture
def mailpit() -> Iterator[MailpitClient]:
    with MailpitClient() as client:
        client.delete_all_messages()
        yield client
