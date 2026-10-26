import hashlib
import io

import pytest
import structlog
from facebook_business.adobjects.serverside.event import Event
from fastapi import BackgroundTasks, Request

# all sends are mocked; credentials are only needed to import the helper
with pytest.MonkeyPatch.context() as credentials:
    credentials.setenv("META_PIXEL_ID", "test-pixel")
    credentials.setenv("META_PIXEL_KEY", "test-key")
    import app.helpers.facebook as fb


# TODO this should be in the structlog_config module
@pytest.fixture
def capture_structlog_logs():
    """
    Fixture that provides a logger and access to its output.
    Returns a tuple of (log, capture).
    """

    from structlog_config import configure_logger

    output = io.StringIO()

    log = configure_logger(logger_factory=structlog.PrintLoggerFactory(file=output))
    log.clear()

    yield log, output


def make_request(
    *,
    path: str = "/screening",
    query_string: str = "",
    user_agent: str = "pytest-agent",
    cookies: str | None = None,
    host: str = "example.com",
) -> Request:
    headers: list[tuple[bytes, bytes]] = [
        (b"user-agent", user_agent.encode()),
        (b"host", host.encode()),
    ]
    if cookies:
        headers.append((b"cookie", cookies.encode()))

    scope = {
        "type": "http",
        "http_version": "1.1",
        "method": "GET",
        "scheme": "https",
        "server": ("example.com", 443),
        "client": ("203.0.113.10", 5150),
        "path": path,
        "raw_path": path.encode(),
        "query_string": query_string.encode(),
        "headers": headers,
    }

    return Request(scope)


class FakeEventRequest:
    def __init__(
        self,
        sent: list[dict],
        error: RuntimeError | None,
        *,
        pixel_id: str,
        events: list[Event],
        test_event_code: str | None = None,
    ):
        self.sent = sent
        self.error = error
        self.pixel_id = pixel_id
        self.events = events
        self.test_event_code = test_event_code

    def execute(self):
        if self.error:
            raise self.error

        payload: dict = {"data": [event.normalize() for event in self.events]}
        if self.test_event_code:
            payload["test_event_code"] = self.test_event_code
        self.sent.append(payload)


def setup_facebook_mocks(monkeypatch, *, error: RuntimeError | None = None):
    # avoid real SDK init
    class _NoopApi:
        @staticmethod
        def init(**_kwargs):
            return None

    monkeypatch.setattr(fb, "FacebookAdsApi", _NoopApi)

    sent: list[dict] = []
    monkeypatch.setattr(
        fb,
        "EventRequest",
        lambda **kwargs: FakeEventRequest(sent, error, **kwargs),
    )

    return sent


def test_pageview_sends_event_with_query_params_preferred(monkeypatch):
    sent = setup_facebook_mocks(monkeypatch)

    request = make_request(
        path="/screening",
        query_string="fbp=ABC123&fbc=fb.1.1234567890.CLICKID.AQIAAQMA",
    )

    fb.send_conversion_event(event_name="PageView", request=request)

    data = sent[0]["data"][0]
    assert data["event_name"] == "PageView"
    assert data["action_source"] == fb.ActionSource.WEBSITE.value
    assert str(request.url) in data["event_source_url"]
    assert isinstance(data["event_time"], int)

    # user data
    user = data["user_data"]
    assert user["fbp"] == "ABC123"
    assert user["fbc"] == "fb.1.1234567890.CLICKID.AQIAAQMA"


def test_purchase_sends_event_with_cookie_fallback(monkeypatch):
    sent = setup_facebook_mocks(monkeypatch)

    # cookies only, no query params
    request = make_request(
        cookies="_fbp=FBP_COOKIE; _fbc=FBC_COOKIE",
    )

    fb.send_conversion_event(
        event_name="Purchase", request=request, value_in_cents=1234, currency="USD"
    )

    data = sent[0]["data"][0]
    user = data["user_data"]
    assert user["fbp"] == "FBP_COOKIE"
    assert user["fbc"] == "FBC_COOKIE"

    custom = data["custom_data"]
    assert custom["value"] == 12.34
    assert custom["currency"] == "usd"


def test_missing_attribution_does_not_generate_browser_id(monkeypatch):
    sent = setup_facebook_mocks(monkeypatch)

    fb.send_conversion_event(
        event_name="PageView",
        request=make_request(),
        email="viewer@example.com",
    )

    user = sent[0]["data"][0]["user_data"]
    assert "fbp" not in user
    assert "fbc" not in user


def test_fbclid_is_expanded_into_fbc(monkeypatch):
    sent = setup_facebook_mocks(monkeypatch)

    request = make_request(query_string="fbclid=CLICKID", host="militia.movie")

    fb.send_conversion_event(event_name="PageView", request=request)

    # subdomain index of 1 means the cookie belongs on the eTLD+1, and the trailing
    # appendix is the version metadata Meta expects on server-generated click ids
    fbc = sent[0]["data"][0]["user_data"]["fbc"]
    assert fbc.startswith("fb.1.")
    assert ".CLICKID." in fbc


def test_resolve_fbc_uses_forwarded_tracking_params_when_request_has_none():
    """
    `/pending` and `/free-access` are XHRs: the ad click is on the page URL, never on the request.
    The frontend forwards it in the body, and that has to beat the cookie-only fallback.
    """

    request = make_request(path="/streaming/pending")
    fbc = fb.resolve_fbc(request, {"fbclid": "CLICKID"})

    assert fbc is not None
    assert fbc.startswith("fb.1.")
    assert ".CLICKID." in fbc


def test_resolve_fbc_prefers_forwarded_click_over_stale_cookie():
    "the `_fbc` cookie lives ~90 days, so it can hold an older click than the one that just landed"

    request = make_request(path="/streaming/pending", cookies="_fbc=fb.1.111.OLDCLICK")
    fbc = fb.resolve_fbc(request, {"fbclid": "NEWCLICK"})

    assert fbc is not None
    assert ".NEWCLICK." in fbc


def test_resolve_fbc_falls_back_to_cookie_without_forwarded_params():
    "orders created before the frontend started forwarding params still resolve"

    request = make_request(path="/streaming/pending", cookies="_fbc=FBC_COOKIE")

    assert fb.resolve_fbc(request) == "FBC_COOKIE"
    assert fb.resolve_fbc(request, {}) == "FBC_COOKIE"


def test_invalid_phone_drops_only_the_phone(monkeypatch):
    sent = setup_facebook_mocks(monkeypatch)

    fb.send_conversion_event(
        event_name="Purchase",
        request=make_request(),
        email="buyer@example.com",
        phone="not a phone number",
    )

    # the event still has to reach Meta; an unusable phone costs us one match key, not the sale
    user = sent[0]["data"][0]["user_data"]
    assert "ph" not in user
    assert user["em"]


def test_valid_phone_is_hashed_in_e164(monkeypatch):
    sent = setup_facebook_mocks(monkeypatch)

    fb.send_conversion_event(
        event_name="Purchase",
        request=make_request(),
        phone="(415) 626-3335",
    )

    # the country code has to be prepended before hashing or the match key never lines up
    expected = hashlib.sha256(b"14156263335").hexdigest()

    assert sent[0]["data"][0]["user_data"]["ph"] == [expected]


def test_send_failure_logs_exception(monkeypatch, capture_structlog_logs):
    log, output = capture_structlog_logs

    import app.helpers.facebook

    monkeypatch.setattr(app.helpers.facebook, "log", log)
    captured = []
    monkeypatch.setattr(
        fb.sentry_sdk, "capture_exception", lambda: captured.append(True)
    )

    setup_facebook_mocks(monkeypatch, error=RuntimeError("boom"))

    request = make_request()
    fb.send_conversion_event(event_name="PageView", request=request)

    logs = output.getvalue()

    assert "facebook pixel event send failed" in logs
    assert "PageView" in logs

    # the traceback is the whole point: a swallowed send is invisible without it
    assert "RuntimeError" in logs
    assert "Traceback" in logs
    assert captured == [True]


def test_phone_uses_buyers_country(monkeypatch):
    sent = setup_facebook_mocks(monkeypatch)

    fb.send_conversion_event(
        event_name="Purchase",
        request=make_request(),
        phone="22 622 15 00",
        country="pl",
    )

    assert sent[0]["data"][0]["user_data"]["ph"] == [
        hashlib.sha256(b"48226221500").hexdigest()
    ]


def test_explicit_fbc_survives_redirect(monkeypatch):
    sent = setup_facebook_mocks(monkeypatch)

    fb.send_conversion_event(
        event_name="Purchase",
        request=make_request(cookies="_fbc=STALE_COOKIE"),
        fbc="fb.1.1234567890000.SAVED_CLICK",
        event_id="order-123",
    )

    event = sent[0]["data"][0]
    assert event["user_data"]["fbc"] == "fb.1.1234567890000.SAVED_CLICK"
    assert event["event_id"] == "order-123"


@pytest.mark.asyncio
async def test_background_send_preserves_test_event_code(monkeypatch):
    sent = setup_facebook_mocks(monkeypatch)
    monkeypatch.setattr(fb, "TEST_EVENT_CODE_OVERRIDE", None)
    tasks = BackgroundTasks()

    fb.set_test_event_code("TEST123")
    fb.send_conversion_event(
        event_name="PageView", request=make_request(), background_tasks=tasks
    )
    fb.set_test_event_code(None)
    assert sent == []

    await tasks()

    assert sent[0]["test_event_code"] == "TEST123"
    fb.send_conversion_event(event_name="PageView", request=make_request())
    assert "test_event_code" not in sent[1]
