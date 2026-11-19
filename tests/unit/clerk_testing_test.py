from types import SimpleNamespace
from typing import Any, cast

import httpx
import pytest
from clerk_backend_api.models.sdkerror import SDKError
from playwright.sync_api import Page

from tests.integration import clerk as clerk_helpers


class FakeResponse:
    def __init__(
        self,
        status: int = 200,
        json_data: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        text_body: str = "",
    ):
        self.status = status
        self._json_data = json_data or {}
        self.headers = headers or {}
        self._text_body = text_body

    def json(self) -> dict[str, Any]:
        return self._json_data

    def text(self) -> str:
        return self._text_body


class FakeRoute:
    def __init__(self, responses: list[FakeResponse | Exception]):
        self._responses = list(responses)
        self.fetch_urls: list[str] = []
        self.fulfilled: list[tuple[FakeResponse | None, Any]] = []
        self.continued_urls: list[str | None] = []

    def fetch(self, *, url: str) -> FakeResponse:
        self.fetch_urls.append(url)
        item = self._responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item

    def fulfill(
        self, *, response: FakeResponse | None = None, json: Any = None
    ) -> None:
        self.fulfilled.append((response, json))

    def continue_(self, *, url: str | None = None) -> None:
        self.continued_urls.append(url)


class FakeContext:
    def __init__(self):
        self.routes: list[tuple[Any, Any]] = []
        self.unrouted: list[Any] = []

    def route(self, pattern: Any, handler: Any) -> None:
        self.routes.append((pattern, handler))

    def unroute(self, pattern: Any) -> None:
        self.unrouted.append(pattern)


class FakePage:
    def __init__(self, context: FakeContext | None = None):
        self.context = context or FakeContext()
        self.wait_timeouts: list[float] = []
        self._closed = False

    def is_closed(self) -> bool:
        return self._closed

    def wait_for_timeout(self, timeout: float) -> None:
        self.wait_timeouts.append(timeout)


def test_setup_clerk_testing_token_deduplicates_context_and_tears_down(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("CLERK_FAPI", "clerk.example.com")
    monkeypatch.setenv("CLERK_TESTING_TOKEN", "tok_test")

    ctx = FakeContext()
    page1 = FakePage(ctx)
    page2 = FakePage(ctx)

    clerk_helpers.setup_clerk_testing_token(cast(Page, page1))
    clerk_helpers.setup_clerk_testing_token(cast(Page, page2))

    assert len(ctx.routes) == 1

    clerk_helpers.teardown_clerk_testing_token(cast(Page, page1))
    assert len(ctx.unrouted) == 1

    clerk_helpers.setup_clerk_testing_token(cast(Page, page2))
    assert len(ctx.routes) == 2


def test_route_retries_transient_status_and_overrides_captcha_bypass(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("CLERK_FAPI", "clerk.example.com")
    monkeypatch.setenv("CLERK_TESTING_TOKEN", "tok_test")
    monkeypatch.setattr(clerk_helpers.random, "uniform", lambda _a, _b: 0.0)

    page = FakePage()
    clerk_helpers.setup_clerk_testing_token(cast(Page, page))
    _, handler = page.context.routes[0]

    route = FakeRoute(
        [
            FakeResponse(status=429),
            FakeResponse(status=503),
            FakeResponse(
                status=200,
                json_data={
                    "response": {"captcha_bypass": False},
                    "client": {"captcha_bypass": False},
                },
            ),
        ]
    )
    request = SimpleNamespace(url="https://clerk.example.com/v1/client?foo=1")

    handler(route, request)

    assert len(route.fetch_urls) == 3
    assert "__clerk_testing_token=tok_test" in route.fetch_urls[0]
    assert page.wait_timeouts == [500, 1000]
    assert len(route.fulfilled) == 1
    _, fulfilled_json = route.fulfilled[0]
    assert fulfilled_json["response"]["captcha_bypass"] is True
    assert fulfilled_json["client"]["captcha_bypass"] is True


def test_route_logs_diagnostics_when_status_retries_exhausted(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("CLERK_FAPI", "clerk.example.com")
    monkeypatch.setenv("CLERK_TESTING_TOKEN", "tok_test")
    monkeypatch.setattr(clerk_helpers.random, "uniform", lambda _a, _b: 0.0)

    warnings: list[str] = []
    monkeypatch.setattr(
        clerk_helpers.logger,
        "warning",
        lambda msg, *args: warnings.append(msg % args if args else msg),
    )

    page = FakePage()
    clerk_helpers.setup_clerk_testing_token(cast(Page, page))
    _, handler = page.context.routes[0]

    last_response = FakeResponse(
        status=429,
        headers={"cf-ray": "ray-123", "retry-after": "5", "content-type": "text/plain"},
        text_body="x" * 700,
    )
    route = FakeRoute(
        [
            FakeResponse(status=429),
            FakeResponse(status=429),
            FakeResponse(status=429),
            last_response,
        ]
    )
    request = SimpleNamespace(url="https://clerk.example.com/v1/client")

    handler(route, request)

    assert len(route.fetch_urls) == 4
    assert page.wait_timeouts == [500, 1000, 2000]
    assert route.fulfilled == [(last_response, None)]
    assert route.continued_urls == []
    assert len(warnings) == 1
    assert "cf-ray: ray-123" in warnings[0]
    assert f"body: {'x' * 500}" in warnings[0]
    assert "x" * 501 not in warnings[0]


def test_route_retries_fetch_errors_and_falls_back_to_continue(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("CLERK_FAPI", "clerk.example.com")
    monkeypatch.setenv("CLERK_TESTING_TOKEN", "tok_test")
    monkeypatch.setattr(clerk_helpers.random, "uniform", lambda _a, _b: 0.0)

    warnings: list[str] = []
    monkeypatch.setattr(
        clerk_helpers.logger,
        "warning",
        lambda msg, *args: warnings.append(msg % args if args else msg),
    )

    page = FakePage()
    clerk_helpers.setup_clerk_testing_token(cast(Page, page))
    _, handler = page.context.routes[0]

    route = FakeRoute([RuntimeError("boom")] * 4)
    request = SimpleNamespace(url="https://clerk.example.com/v1/client")

    handler(route, request)

    assert len(route.fetch_urls) == 4
    assert page.wait_timeouts == [500, 1000, 2000]
    assert route.fulfilled == []
    assert route.continued_urls == [
        "https://clerk.example.com/v1/client?__clerk_testing_token=tok_test"
    ]
    assert len(warnings) == 1
    assert "failed after 4 attempts" in warnings[0]


def test_create_testing_token_with_retry_handles_429_and_transport_error(
    monkeypatch: pytest.MonkeyPatch,
):
    sleeps: list[float] = []
    monkeypatch.setattr(clerk_helpers.time, "sleep", sleeps.append)
    monkeypatch.setattr(clerk_helpers.random, "uniform", lambda _a, _b: 0.0)

    rate_limited = httpx.Response(
        429,
        headers={"retry-after": "2", "content-type": "application/json"},
        text="rate limited",
    )
    attempts = [
        SDKError("rate limited", rate_limited),
        httpx.ConnectError("transient"),
        SimpleNamespace(token="tok_recovered"),
    ]

    def fake_create() -> Any:
        item = attempts.pop(0)
        if isinstance(item, Exception):
            raise item
        return item

    fake_client = cast(
        clerk_helpers.Clerk,
        SimpleNamespace(testing_tokens=SimpleNamespace(create=fake_create)),
    )

    token = clerk_helpers._create_testing_token_with_retry(fake_client)

    assert token == "tok_recovered"
    assert sleeps == [2.0, 2.0]
