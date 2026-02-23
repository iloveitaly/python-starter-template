"""
This test suite intentionally does not use factory models. This is to avoid testing business logic
around when webhooks should be fired and instead focus the testing on the core webhook logic.
"""

# pytest skip
import pytest

pytest.skip("Skipping unit tests for webhook processing logic", allow_module_level=True)

from datetime import datetime, timezone

import httpx
import pytest
from celery.exceptions import Retry
from typeid import TypeID

import app.jobs.process_webhook

from app.models.ticket_reservation_order import WebhookBase
from app.models.webhook_event import WebhookEvent

from tests.factories import (
    DistributionFactory,
    HostScreeningOrderFactory,
    TicketReservationOrderFactory,
)


def test_queue_webhook_skips_when_no_endpoint():
    distribution = DistributionFactory.save(webhook_endpoint=None)

    random_fake_object_id = TypeID(prefix="ob")

    class TestWebhook(WebhookBase):
        pass

    TestWebhook(
        type="ticket_reservation_order.created",
        distribution_id=distribution.id,
        id=random_fake_object_id,
    ).queue_webhook()

    assert WebhookEvent.count() == 0


def test_queue_webhook_enqueues_and_processes_success(respx_mock, sync_celery):
    webhook_endpoint = "https://example.com/webhook"
    distribution = DistributionFactory.save(webhook_endpoint=webhook_endpoint)

    webhook_route = respx_mock.post(webhook_endpoint).mock(
        return_value=httpx.Response(200, json={"status": "received"})
    )

    random_fake_object_id = TypeID(prefix="ob")

    class TestWebhook(WebhookBase):
        pass

    # since sync_celery is used, the webhook will be processed eagerly
    TestWebhook(
        type="ticket_reservation_order.created",
        distribution_id=distribution.id,
        id=random_fake_object_id,
    ).queue_webhook()

    assert WebhookEvent.count() == 1

    webhook = WebhookEvent.first()

    assert webhook.destination == webhook_endpoint
    assert webhook.type == "ticket_reservation_order.created"
    assert webhook.succeeded_at is not None
    assert webhook.failed_at is None
    assert webhook.response_payload == {"status": "received"}
    assert webhook.originating_id == random_fake_object_id.uuid
    assert webhook.distribution_id == distribution.id
    assert webhook.payload == {
        "type": "ticket_reservation_order.created",
        "id": str(random_fake_object_id),
        "distribution_id": str(distribution.id),
    }

    assert webhook_route.called


def test_process_webhook_skips_if_already_succeeded(respx_mock):
    distribution = DistributionFactory.save()
    distribution.webhook_endpoint = "https://example.com/webhook"
    distribution.save()

    random_fake_object_id = TypeID(prefix="ob")

    class TestWebhook(WebhookBase):
        pass

    webhook_data = TestWebhook(
        type="ticket_reservation_order.updated",
        distribution_id=distribution.id,
        id=random_fake_object_id,
    )

    event = WebhookEvent.from_webhook_data(webhook_data)
    event.succeeded_at = datetime.now(timezone.utc)
    event.save()

    # httpx.post should not be called when already succeeded, so no mock needed
    app.jobs.process_webhook.perform(event.id)


def test_process_webhook_records_json_response_payload(respx_mock, sync_celery):
    distribution = DistributionFactory.save()
    distribution.webhook_endpoint = "https://example.com/webhook"
    distribution.save()

    expected_response_payload = {"status": "received", "order_id": "test_order_id"}

    webhook_route = respx_mock.post(distribution.webhook_endpoint).mock(
        return_value=httpx.Response(200, json=expected_response_payload)
    )

    random_fake_object_id = TypeID(prefix="ob")

    class TestWebhook(WebhookBase):
        pass

    webhook_data = TestWebhook(
        type="ticket_reservation_order.created",
        distribution_id=distribution.id,
        id=random_fake_object_id,
    )

    event = WebhookEvent.from_webhook_data(webhook_data)

    app.jobs.process_webhook.perform(event.id)

    # event updated by the webhook processing
    event.refresh()

    assert event.response_payload == expected_response_payload
    assert event.succeeded_at is not None
    assert event.failed_at is None
    assert webhook_route.called


@pytest.mark.skip(reason="sync_celery causes retries to be run inline")
def test_process_webhook_records_empty_dict_for_non_json_response(
    respx_mock, sync_celery
):
    distribution = DistributionFactory.save()
    distribution.webhook_endpoint = "https://example.com/webhook"
    distribution.save()

    # Create a response that will raise an exception when json() is called
    def mock_response(request):
        response = httpx.Response(200, text="invalid json {")
        # Monkey patch the json method to raise an exception
        original_json = response.json

        def failing_json():
            try:
                return original_json()
            except Exception:
                raise ValueError("Not valid JSON")

        response.json = failing_json
        return response

    webhook_route = respx_mock.post(distribution.webhook_endpoint).mock(
        side_effect=mock_response
    )

    random_fake_object_id = TypeID(prefix="ob")

    class TestWebhook(WebhookBase):
        pass

    webhook_data = TestWebhook(
        type="ticket_reservation_order.created",
        distribution_id=distribution.id,
        id=random_fake_object_id,
    )

    event = WebhookEvent.from_webhook_data(webhook_data)

    # This should cause a retry since the response isn't valid JSON
    with pytest.raises(Retry):
        app.jobs.process_webhook.perform(event.id)

    # event updated by the webhook processing
    event.refresh()

    assert event.response_payload is None
    assert event.succeeded_at is None
    assert event.failed_at is not None
    assert webhook_route.called


def test_process_webhook_handles_empty_response_body(respx_mock, sync_celery):
    distribution = DistributionFactory.save()
    distribution.webhook_endpoint = "https://example.com/webhook"
    distribution.save()

    webhook_route = respx_mock.post(distribution.webhook_endpoint).mock(
        return_value=httpx.Response(200, json={})
    )

    random_fake_object_id = TypeID(prefix="ob")

    class TestWebhook(WebhookBase):
        pass

    webhook_data = TestWebhook(
        type="ticket_reservation_order.created",
        distribution_id=distribution.id,
        id=random_fake_object_id,
    )

    event = WebhookEvent.from_webhook_data(webhook_data)

    app.jobs.process_webhook.perform(event.id)

    # event updated by the webhook processing
    event.refresh()

    assert event.response_payload == {}
    assert event.succeeded_at is not None
    assert event.failed_at is None
    assert webhook_route.called


def test_process_webhook_errors_on_invalid_host(respx_mock, sync_celery, monkeypatch):
    monkeypatch.setattr(app.jobs.process_webhook, "DEFAULT_WEBHOOK_TIMEOUT", 1)

    distribution = DistributionFactory.save(
        webhook_endpoint="https://nonexistent.invalid/webhook"
    )

    # Mock the connection error by raising an exception in the side_effect
    def mock_connect_error(request):
        raise httpx.ConnectError("Connection failed")

    webhook_route = respx_mock.post(distribution.webhook_endpoint).mock(
        side_effect=mock_connect_error
    )

    random_fake_object_id = TypeID(prefix="ob")

    class TestWebhook(WebhookBase):
        pass

    webhook_data = TestWebhook(
        type="ticket_reservation_order.created",
        distribution_id=distribution.id,
        id=random_fake_object_id,
    )

    event = WebhookEvent.from_webhook_data(webhook_data)

    # TODO we should really use a separate worker to test the retry stuff
    # retries don't operate when in sync mode
    with pytest.raises(httpx.ConnectError):
        app.jobs.process_webhook.perform(event.id)

    # event updated to failed by the webhook processing
    event.refresh()

    assert event.destination == distribution.webhook_endpoint
    assert event.type == "ticket_reservation_order.created"
    assert event.failed_at is not None
    assert event.succeeded_at is None
    assert event.response_payload is None
    assert webhook_route.called


def test_queue_webhook_skips_when_host_order_with_same_email(respx_mock):
    distribution = DistributionFactory.save(
        webhook_endpoint="https://example.com/webhook"
    )

    email = "skipme@example.com"

    # existing host order with the same email
    host_order = HostScreeningOrderFactory.save(distribution_id=distribution.id)
    host_order.form_data["email"] = email
    # TODO should automatically do this
    host_order.flag_modified("form_data")
    host_order.save()

    order = TicketReservationOrderFactory.save(
        distribution_id=distribution.id, email=email
    )

    # pre-conditions
    assert host_order.form_data["email"] == order.email
    assert order.email == email

    # httpx.post should not be called when webhook is skipped, so no mock needed

    # should be skipped due to existing host order with same email
    order.webhook("ticket_reservation_order.created").queue_webhook()

    assert (
        WebhookEvent.where(WebhookEvent.distribution_id == distribution.id).count() == 0
    )
