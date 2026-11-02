import json
import traceback

import sentry_sdk
from requests.exceptions import ConnectionError as RequestsConnectionError
from urllib3.exceptions import MaxRetryError

from app.lib.secret_redaction import (
    FILTERED_SECRET,
    redact_exception_chain,
    scrub_access_token,
    scrub_sentry_event,
)

TOKEN = "EAAMSECRETZDZD"
GRAPH_URL = (
    f"https://graph.facebook.com/v26.0/1103726080810040/events?access_token={TOKEN}"
)


def test_scrub_access_token_keeps_surrounding_query_parameters():
    scrubbed = scrub_access_token(f"{GRAPH_URL}&foo=1")

    assert TOKEN not in scrubbed
    assert f"access_token={FILTERED_SECRET}" in scrubbed
    assert "1103726080810040" in scrubbed
    assert "foo=1" in scrubbed


def test_scrub_sentry_event_redacts_exception_text_and_frame_vars():
    event = {
        "exception": {
            "values": [
                {
                    "type": "MaxRetryError",
                    "value": f"Max retries exceeded with url: {GRAPH_URL} (Caused by OSError)",
                    "stacktrace": {
                        "frames": [
                            {
                                "vars": {
                                    "url": GRAPH_URL,
                                    "access_token": TOKEN,
                                    "method": "POST",
                                }
                            }
                        ]
                    },
                }
            ]
        },
        "breadcrumbs": {
            "values": [{"message": f"request {GRAPH_URL}&foo=1"}],
        },
        "spans": [{"data": {"http.query": f"access_token={TOKEN}&foo=1"}}],
    }

    scrub_sentry_event(event, {})

    rendered = json.dumps(event)
    frame_vars = event["exception"]["values"][0]["stacktrace"]["frames"][0]["vars"]

    assert TOKEN not in rendered
    assert f"access_token={FILTERED_SECRET}" in rendered
    assert frame_vars["access_token"] == FILTERED_SECRET
    assert frame_vars["method"] == "POST"
    assert "foo=1" in rendered
    assert "1103726080810040" in rendered


def test_redact_exception_chain_scrubs_requests_connection_error():
    class PreparedRequest:
        def __init__(self):
            self.url = GRAPH_URL

    try:
        try:
            raise MaxRetryError(None, GRAPH_URL, OSError(101, "Network is unreachable"))
        except MaxRetryError as retry_error:
            raise RequestsConnectionError(retry_error, request=PreparedRequest())
    except RequestsConnectionError as exc:
        redact_exception_chain(exc)
        rendered = "".join(traceback.format_exception(exc))
        retry_url = exc.args[0].url
        request_url = exc.request.url

    assert TOKEN not in rendered
    assert f"access_token={FILTERED_SECRET}" in rendered
    assert "1103726080810040" in rendered
    assert TOKEN not in retry_url
    assert TOKEN not in request_url


def test_sentry_hooks_scrub_events_and_still_drop_healthchecks():
    client = sentry_sdk.get_client()

    error_event = {"message": f"failed {GRAPH_URL}"}
    assert client.options["before_send"](error_event, {}) == error_event
    assert TOKEN not in json.dumps(error_event)

    dropped = client.options["before_send_transaction"](
        {"request": {"url": f"https://example.com/healthcheck?access_token={TOKEN}"}},
        {},
    )
    assert dropped is None

    kept = client.options["before_send_transaction"](
        {
            "request": {"url": f"https://example.com/screenings?access_token={TOKEN}"},
            "message": GRAPH_URL,
        },
        {},
    )
    assert kept is not None
    assert TOKEN not in json.dumps(kept)
    assert "/screenings" in kept["request"]["url"]
