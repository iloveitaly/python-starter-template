"""
TODO needs more refinement before it's ready for prime time, pull in tests from movie project

Example payload:

>>> to_json(StreamingOrder.sample().webhook('streaming_order.created').payload())
>>> to_json(StreamingOrder.sample().webhook("streaming_order.created").model_json_schema())
"""

from datetime import datetime
from typing import Literal, get_args
from uuid import UUID

from pydantic import BaseModel as PydanticBaseModel

import app.jobs.process_webhook
from app import log

from activemodel import BaseModel
from activemodel.mixins import TimestampsMixin, TypeIDMixin
from activemodel.types import TypeIDType
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field

WebhookTypesType = Literal["order.created"]

# convert the literal types into a nice array that we can use
WebhookTypes: list[str] = list(get_args(WebhookTypesType))

# Fallback webhook endpoint used when no distribution endpoint is available.
# Keep at module level so it can be easily changed or exported later.
DEFAULT_WEBHOOK_ENDPOINT = "https://example.com/webhook"


class WebhookBase(PydanticBaseModel):
    """
    Intermediate abstract base class meant to customize a payload structure for a specific model and type
    """

    type: WebhookTypesType
    id: TypeIDType

    def payload(self) -> dict:
        "generates a JSON of the more complex data payload model structure in your subclass"

        return self.model_dump(mode="json")

    def queue_webhook(self):
        """
        Create a webhook event record and queue it for delivery.
        """
        assert self.type in WebhookTypes, f"Invalid webhook type: {self.type}"

        event = WebhookEvent.from_webhook_data(self)

        log.info(
            "queuing webhook",
            event_id=event.id,
            destination=event.destination,
            event_type=event.type,
        )

        app.jobs.process_webhook.queue(event.id)


class WebhookEvent(BaseModel, TimestampsMixin, TypeIDMixin("wh"), table=True):
    """Represents an outbound webhook queued for delivery."""

    destination: str
    "HTTP endpoint that will receive the webhook POST"

    # TODO https://github.com/fastapi/sqlmodel/pull/1439 use the literal type above
    type: str = Field(index=True, min_length=1)
    "application event name (e.g. 'ticket.paid') used for routing/observability"

    payload: dict = Field(sa_type=JSONB)
    "JSON body sent to destination as the POST request payload"

    failed_at: datetime | None = None
    "timestamp of the last failed delivery attempt"

    succeeded_at: datetime | None = None
    "timestamp when delivery last succeeded (used to prevent resends)"

    originating_id: UUID | None = Field(default=None, index=True)
    "identifier of the domain object this event refers to, if any"

    response_payload: dict | None = Field(sa_type=JSONB, default=None)
    "JSON body received from the destination as the POST response payload"

    @classmethod
    def from_webhook_data(cls, webhook_data: WebhookBase) -> "WebhookEvent":
        """
        Create a new WebhookEvent record from webhook data.
        """
        return cls(
            destination=DEFAULT_WEBHOOK_ENDPOINT,
            type=webhook_data.type,
            payload=webhook_data.payload(),
            originating_id=webhook_data.id.uuid,
        ).save()
