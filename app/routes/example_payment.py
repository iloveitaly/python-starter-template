"""
Example Checkout payment used to exercise `app.lib.stripe` helpers.

This does not persist an order. Stripe remains the source of truth so the page
can run without a new table. A saved order would need a migration.
"""

from fastapi import APIRouter, Query
from pydantic import BaseModel
from stripe import PaymentIntent
from stripe.checkout import Session as CheckoutSession

from app import log
from app.configuration.stripe import stripe_client
from app.env import env
from app.lib.stripe import (
    extract_checkout_session_id_from_client_secret,
    extract_country_zip_from_checkout_session,
    payment_intent_is_disputed,
    stripe_retrieve,
)
from app.routes.errors import ClientError

EXAMPLE_PAYMENT_AMOUNT_CENTS = 5_00
EXAMPLE_PAYMENT_CURRENCY = "usd"
EXAMPLE_PAYMENT_PRODUCT_NAME = "Example payment"

example_payment_api = APIRouter(prefix="/example-payment")


def example_payment_return_url() -> str:
    # CHECKOUT_SESSION_ID is Stripe's placeholder and must stay unescaped
    frontend_base = env.base_url("VITE_APP_BASE_URL")
    return f"{frontend_base}pay/confirmation?session_id={{CHECKOUT_SESSION_ID}}"


def payment_intent_id_from_session(session: CheckoutSession) -> str:
    payment_intent = session.payment_intent
    assert payment_intent

    if isinstance(payment_intent, PaymentIntent):
        return payment_intent.id

    assert isinstance(payment_intent, str)
    return payment_intent


class CreateExamplePaymentSessionResponse(BaseModel, extra="forbid"):
    client_secret: str
    amount_cents: int
    currency: str
    product_name: str


class ExamplePaymentPendingRequest(BaseModel, extra="forbid"):
    client_secret: str


class ExamplePaymentPendingResponse(BaseModel, extra="forbid"):
    stripe_checkout_session_id: str


class ExamplePaymentStatusResponse(BaseModel, extra="forbid"):
    stripe_checkout_session_id: str
    payment_intent_id: str
    disputed: bool
    country: str | None = None
    postal_code: str | None = None
    amount_cents: int
    currency: str


@example_payment_api.post("/session")
def create_example_payment_session() -> CreateExamplePaymentSessionResponse:
    """
    Create a Checkout Session when the example payment page loads.

    The browser confirms this session with Stripe.js. `return_url` is where Stripe
    sends the browser after a redirect-based payment method.
    """

    client = stripe_client()
    session = client.v1.checkout.sessions.create(
        params={
            # elements matches stripe.js initCheckoutElementsSdk
            "ui_mode": "elements",
            "mode": "payment",
            "billing_address_collection": "required",
            "line_items": [
                {
                    "quantity": 1,
                    "price_data": {
                        "currency": EXAMPLE_PAYMENT_CURRENCY,
                        "unit_amount": EXAMPLE_PAYMENT_AMOUNT_CENTS,
                        "product_data": {"name": EXAMPLE_PAYMENT_PRODUCT_NAME},
                    },
                }
            ],
            "return_url": example_payment_return_url(),
        }
    )

    client_secret = session.client_secret
    assert client_secret

    amount_cents = session.amount_total
    assert amount_cents is not None

    currency = session.currency
    assert currency

    log.info("created example payment session", session_id=session.id)

    return CreateExamplePaymentSessionResponse(
        client_secret=client_secret,
        amount_cents=amount_cents,
        currency=currency,
        product_name=EXAMPLE_PAYMENT_PRODUCT_NAME,
    )


@example_payment_api.post("/pending")
def create_example_payment_pending(
    data: ExamplePaymentPendingRequest,
) -> ExamplePaymentPendingResponse:
    """
    Validate the checkout session is still open before the browser confirms payment.

    The client secret is parsed with the stripe helper so a tampered secret never
    reaches Stripe. This can run again if confirmation fails and the buyer retries.
    """

    session_id = extract_checkout_session_id_from_client_secret(data.client_secret)
    session = stripe_retrieve(session_id, stripe_client())
    assert isinstance(session, CheckoutSession)

    if session.status != "open":
        raise ClientError(
            "Your checkout session has expired. Please refresh the page and try again.",
        )

    return ExamplePaymentPendingResponse(stripe_checkout_session_id=session_id)


@example_payment_api.get("/status")
def example_payment_status(
    session_id: str = Query(),
) -> ExamplePaymentStatusResponse:
    """
    Read a completed checkout session for the confirmation page.

    Country and postal code come from the checkout helper. Dispute state comes from
    the payment intent helper.
    """

    client = stripe_client()
    session = stripe_retrieve(session_id, client)
    assert isinstance(session, CheckoutSession)

    if session.status != "complete":
        raise ClientError(
            "Checkout is not complete. Return to the payment page and try again.",
        )

    payment_intent_id = payment_intent_id_from_session(session)
    disputed = payment_intent_is_disputed(client, payment_intent_id)
    country_zip = extract_country_zip_from_checkout_session(client, session_id)

    amount_cents = session.amount_total
    assert amount_cents is not None

    currency = session.currency
    assert currency

    assert session.id

    return ExamplePaymentStatusResponse(
        stripe_checkout_session_id=session.id,
        payment_intent_id=payment_intent_id,
        disputed=disputed,
        country=country_zip.country,
        postal_code=country_zip.postal_code,
        amount_cents=amount_cents,
        currency=currency,
    )
