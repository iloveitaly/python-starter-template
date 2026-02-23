"""
This test suite intentionally does not use factory models. This is to avoid testing business logic
around when webhooks should be fired and instead focus the testing on the core webhook logic.
"""

from datetime import datetime, timezone

import httpx
import pytest
from celery.exceptions import Retry
from typeid import TypeID

import app.jobs.process_webhook

from app.models.webhook_event import WebhookBase, WebhookEvent


def test_queue_webhook_skips_when_no_endpoint(monkeypatch):
    monkeypatch.setattr("app.models.webhook_event.WEBHOOK_ENDPOINT", None)

    random_fake_object_id = TypeID(prefix="ob")

    class TestWebhook(WebhookBase):
        pass

    TestWebhook(
        type="order.created",
        id=random_fake_object_id,
    ).queue_webhook()

    assert WebhookEvent.count() == 0


def test_queue_webhook_enqueues_and_processes_success(
    monkeypatch, httpx_mock, sync_celery
):
    webhook_endpoint = "https://example.com/webhook"
    monkeypatch.setattr("app.models.webhook_event.WEBHOOK_ENDPOINT", webhook_endpoint)

    httpx_mock.add_response(
        method="POST", url=webhook_endpoint, json={"status": "received"}
    )

    random_fake_object_id = TypeID(prefix="ob")

    class TestWebhook(WebhookBase):
        pass

    # since sync_celery is used, the webhook will be processed eagerly
    TestWebhook(
        type="order.created",
        id=random_fake_object_id,
    ).queue_webhook()

    assert WebhookEvent.count() == 1

    webhook = WebhookEvent.first()

    assert webhook.destination == webhook_endpoint
    assert webhook.type == "order.created"
    assert webhook.succeeded_at is not None
    assert webhook.failed_at is None
    assert webhook.response_payload == {"status": "received"}
    assert webhook.originating_id == random_fake_object_id.uuid
    assert webhook.payload == {
        "type": "order.created",
        "id": str(random_fake_object_id),
    }

    assert len(httpx_mock.get_requests()) == 1


def test_process_webhook_skips_if_already_succeeded(monkeypatch, httpx_mock):
    webhook_endpoint = "https://example.com/webhook"
    monkeypatch.setattr("app.models.webhook_event.WEBHOOK_ENDPOINT", webhook_endpoint)

    random_fake_object_id = TypeID(prefix="ob")

    class TestWebhook(WebhookBase):
        pass

    webhook_data = TestWebhook(
        type="order.created",
        id=random_fake_object_id,
    )

    event = WebhookEvent.from_webhook_data(webhook_data, webhook_endpoint)
    event.succeeded_at = datetime.now(timezone.utc)
    event.save()

    # httpx.post should not be called when already succeeded, so no mock needed
    app.jobs.process_webhook.perform(event.id)
    assert len(httpx_mock.get_requests()) == 0


def test_process_webhook_records_json_response_payload(
    monkeypatch, httpx_mock, sync_celery
):
    webhook_endpoint = "https://example.com/webhook"
    monkeypatch.setattr("app.models.webhook_event.WEBHOOK_ENDPOINT", webhook_endpoint)

    expected_response_payload = {"status": "received", "order_id": "test_order_id"}

    httpx_mock.add_response(
        method="POST", url=webhook_endpoint, json=expected_response_payload
    )

    random_fake_object_id = TypeID(prefix="ob")

    class TestWebhook(WebhookBase):
        pass

    webhook_data = TestWebhook(
        type="order.created",
        id=random_fake_object_id,
    )

    event = WebhookEvent.from_webhook_data(webhook_data, webhook_endpoint)

    app.jobs.process_webhook.perform(event.id)

    # event updated by the webhook processing
    event.refresh()

    assert event.response_payload == expected_response_payload
    assert event.succeeded_at is not None
    assert event.failed_at is None
    assert len(httpx_mock.get_requests()) == 1


@pytest.mark.skip(reason="sync_celery causes retries to be run inline")
def test_process_webhook_records_empty_dict_for_non_json_response(
    monkeypatch, httpx_mock, sync_celery
):
    webhook_endpoint = "https://example.com/webhook"
    monkeypatch.setattr("app.models.webhook_event.WEBHOOK_ENDPOINT", webhook_endpoint)

    httpx_mock.add_response(method="POST", url=webhook_endpoint, text="invalid json {")

    random_fake_object_id = TypeID(prefix="ob")

    class TestWebhook(WebhookBase):
        pass

    webhook_data = TestWebhook(
        type="order.created",
        id=random_fake_object_id,
    )

    event = WebhookEvent.from_webhook_data(webhook_data, webhook_endpoint)

    # This should cause a retry since the response isn't valid JSON
    with pytest.raises(Retry):
        app.jobs.process_webhook.perform(event.id)

    # event updated by the webhook processing
    event.refresh()

    assert event.response_payload is None
    assert event.succeeded_at is None
    assert event.failed_at is not None
    assert len(httpx_mock.get_requests()) == 1


def test_process_webhook_handles_empty_response_body(
    monkeypatch, httpx_mock, sync_celery
):
    webhook_endpoint = "https://example.com/webhook"
    monkeypatch.setattr("app.models.webhook_event.WEBHOOK_ENDPOINT", webhook_endpoint)

    httpx_mock.add_response(method="POST", url=webhook_endpoint, json={})

    random_fake_object_id = TypeID(prefix="ob")

    class TestWebhook(WebhookBase):
        pass

    webhook_data = TestWebhook(
        type="order.created",
        id=random_fake_object_id,
    )

    event = WebhookEvent.from_webhook_data(webhook_data, webhook_endpoint)

    app.jobs.process_webhook.perform(event.id)

    # event updated by the webhook processing
    event.refresh()

    assert event.response_payload == {}
    assert event.succeeded_at is not None
    assert event.failed_at is None
    assert len(httpx_mock.get_requests()) == 1


def test_process_webhook_errors_on_invalid_host(httpx_mock, sync_celery, monkeypatch):
    monkeypatch.setattr(app.jobs.process_webhook, "DEFAULT_WEBHOOK_TIMEOUT", 1)

    webhook_endpoint = "https://nonexistent.invalid/webhook"
    monkeypatch.setattr("app.models.webhook_event.WEBHOOK_ENDPOINT", webhook_endpoint)

    httpx_mock.add_exception(
        httpx.ConnectError("Connection failed"), method="POST", url=webhook_endpoint
    )

    random_fake_object_id = TypeID(prefix="ob")

    class TestWebhook(WebhookBase):
        pass

    webhook_data = TestWebhook(
        type="order.created",
        id=random_fake_object_id,
    )

    event = WebhookEvent.from_webhook_data(webhook_data, webhook_endpoint)

    # TODO we should really use a separate worker to test the retry stuff
    # retries don't operate when in sync mode
    with pytest.raises(httpx.ConnectError):
        app.jobs.process_webhook.perform(event.id)

    # event updated to failed by the webhook processing
    event.refresh()

    assert event.destination == webhook_endpoint
    assert event.type == "order.created"
    assert event.failed_at is not None
    assert event.succeeded_at is None
    assert event.response_payload is None
    assert len(httpx_mock.get_requests()) == 1
