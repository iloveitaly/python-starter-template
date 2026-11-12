from enum import StrEnum
from typing import Literal

from activemodel import BaseModel
from activemodel.mixins import TimestampsMixin, TypeIDField, TypeIDPrimaryKey
from sqlmodel import Field


class ExamplePaymentOrderStatus(StrEnum):
    pending = "pending"
    paid = "paid"


class ExamplePaymentOrder(BaseModel, TimestampsMixin, table=True):
    "Order saved before Stripe confirms payment, then marked paid on return"

    id: TypeIDField[Literal["epo"]] = TypeIDPrimaryKey("epo")

    stripe_checkout_session_id: str = Field(unique=True)
    "checkout session id, unique so a retry updates the same pending order"

    email: str
    status: ExamplePaymentOrderStatus = ExamplePaymentOrderStatus.pending
    amount_cents: int
    currency: str
