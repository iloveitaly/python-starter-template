"""
Example Checkout payment.

Follows the four-step flow in commands.md:

1. Create a checkout session when the payment page loads.
2. Save a pending order immediately before Stripe confirms payment.
3. Mark the order paid when Stripe redirects back to `/complete`.
4. Read the order on the confirmation page. That read can happen more than once.
"""

from fastapi import APIRouter, Query, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from stripe import PaymentIntent
from stripe.checkout import Session as CheckoutSession

from app import log
from app.configuration.stripe import stripe_client
from app.env import env
from app.lib.stripe import (
    extract_country_zip_from_checkout_session,
    get_stripe_type_from_id,
    payment_intent_is_disputed,
    stripe_retrieve,
)
from app.routes.errors import ClientError

from app.models.example_payment_order import (
    ExamplePaymentOrder,
    ExamplePaymentOrderStatus,
)

EXAMPLE_PAYMENT_AMOUNT_CENTS = 5_00
EXAMPLE_PAYMENT_CURRENCY = "usd"
EXAMPLE_PAYMENT_PRODUCT_NAME = "Example payment"

example_payment_api = APIRouter(prefix="/example-payment")


def payment_intent_id_from_session(session: CheckoutSession) -> str:
    payment_intent = session.payment_intent
    assert payment_intent

    if isinstance(payment_intent, PaymentIntent):
        return payment_intent.id

    assert isinstance(payment_intent, str)
    return payment_intent


def require_checkout_session_id(stripe_checkout_session_id: str) -> str:
    stripe_type = get_stripe_type_from_id(
        stripe_checkout_session_id, raise_on_missing=False
    )
    if stripe_type != "checkout.sessions":
        raise ClientError("Invalid checkout session")

    return stripe_checkout_session_id


def retrieve_checkout_session(stripe_checkout_session_id: str) -> CheckoutSession:
    session_id = require_checkout_session_id(stripe_checkout_session_id)
    session = stripe_retrieve(session_id, stripe_client)
    assert isinstance(session, CheckoutSession)
    return session


class CreateExamplePaymentSessionResponse(BaseModel, extra="forbid"):
    client_secret: str
    amount_cents: int
    currency: str
    product_name: str


class ExamplePaymentPendingRequest(BaseModel, extra="forbid"):
    stripe_checkout_session_id: str
    email: str


class ExamplePaymentPendingResponse(BaseModel, extra="forbid"):
    order_id: str


class ExamplePaymentStatusResponse(BaseModel, extra="forbid"):
    order_id: str
    email: str
    status: ExamplePaymentOrderStatus
    stripe_checkout_session_id: str
    payment_intent_id: str
    disputed: bool
    country: str | None = None
    postal_code: str | None = None
    amount_cents: int
    currency: str


@example_payment_api.post("/session")
def create_example_payment_session(
    request: Request,
) -> CreateExamplePaymentSessionResponse:
    """
    Create a Checkout Session when the example payment page loads.

    `return_url` is the backend complete route. Stripe replaces `{CHECKOUT_SESSION_ID}`
    and that value must stay unescaped.
    """

    # elements is the current name of the template's ui_mode "custom"
    return_url = (
        str(request.url_for("complete_example_payment"))
        + "?session_id={CHECKOUT_SESSION_ID}"
    )
    session = stripe_client.v1.checkout.sessions.create(
        params={
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
            "return_url": return_url,
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
    Save the order immediately before the browser confirms payment.

    This can run again if Stripe rejects the form and the buyer retries. The unique
    checkout session id keeps those retries on one order.
    """

    session = retrieve_checkout_session(data.stripe_checkout_session_id)

    if session.status != "open":
        raise ClientError(
            "Your checkout session has expired. Please refresh the page and try again.",
        )

    amount_cents = session.amount_total
    assert amount_cents is not None

    currency = session.currency
    assert currency

    order = ExamplePaymentOrder.one_or_none(
        stripe_checkout_session_id=data.stripe_checkout_session_id
    )
    if order:
        order.email = data.email
        order.save()
    else:
        order = ExamplePaymentOrder(
            stripe_checkout_session_id=data.stripe_checkout_session_id,
            email=data.email,
            amount_cents=amount_cents,
            currency=currency,
        ).save()

    return ExamplePaymentPendingResponse(order_id=str(order.id))


@example_payment_api.get("/complete")
def complete_example_payment(session_id: str = Query()) -> RedirectResponse:
    """
    Stripe redirects the browser here after payment.

    Mark the pending order paid, then send the browser to the confirmation page.
    """

    session = retrieve_checkout_session(session_id)
    if session.status != "complete":
        raise ClientError(
            "Checkout is not complete. Return to the payment page and try again.",
            status_code=404,
            code="NOT_FOUND",
        )

    order = ExamplePaymentOrder.one(stripe_checkout_session_id=session_id)
    order.status = ExamplePaymentOrderStatus.paid
    order.save()

    confirmation_url = (
        f"{env.base_url('VITE_APP_BASE_URL')}pay/confirmation?session_id={session_id}"
    )
    return RedirectResponse(url=confirmation_url)


@example_payment_api.get("/status")
def example_payment_status(session_id: str = Query()) -> ExamplePaymentStatusResponse:
    """
    Read a paid order for the confirmation page.

    Country, postal code, and dispute state come from the stripe helpers. This can
    run every time the confirmation page is opened.
    """

    session = retrieve_checkout_session(session_id)
    if session.status != "complete":
        raise ClientError(
            "Checkout is not complete. Return to the payment page and try again.",
        )

    order = ExamplePaymentOrder.one(stripe_checkout_session_id=session_id)
    payment_intent_id = payment_intent_id_from_session(session)
    disputed = payment_intent_is_disputed(stripe_client, payment_intent_id)
    country_zip = extract_country_zip_from_checkout_session(stripe_client, session_id)

    return ExamplePaymentStatusResponse(
        order_id=str(order.id),
        email=order.email,
        status=order.status,
        stripe_checkout_session_id=order.stripe_checkout_session_id,
        payment_intent_id=payment_intent_id,
        disputed=disputed,
        country=country_zip.country,
        postal_code=country_zip.postal_code,
        amount_cents=order.amount_cents,
        currency=order.currency,
    )
