---
mode: agent
---

A Stripe Checkout implementation takes four steps:

1. Create a checkout session. Happens when the user visits the checkout page.
2. Create a pending order. Happens right before the user is sent to Stripe.
3. Complete the order. Happens when the user is redirected back to the app after payment.
4. Check the order status. Happens when the user visits the confirmation page, which could happen multiple times.

Here's an example implementation:

```python
from .configuration import stripe_client, origin_url

@screening_api_app.post("/")
def create_order_session(
    request: Request,
) -> str:
    """
    Creates a checkout session. This happens after the user visits
    the checkout page.
    """
    session = stripe_client.checkout.sessions.create(
        params={
            "ui_mode": "custom",
            "line_items": [
                {
                    "price": "price_123",
                    "quantity": 1,
                }
            ],
            "mode": "payment",
            # CHECKOUT_SESSION_ID is a placeholder for the actual session id, which is replaced by Stripe
            # cannot use include_query_params because the Stripe checkout template variable is escaped
            "return_url": (
                # `request` required for abs URL generation
                str(request.url_for("complete_ticket_purchase"))
                + "?session_id={CHECKOUT_SESSION_ID}"
            ),
        }
    )

    return session.client_secret


class PendingOrderRequest(BaseModel):
    stripe_checkout_session_id: str

    email: str
    # and other fields...


@screening_api_app.post("/pending")
def create_pending_order(
    data: PendingOrderRequest,
    distribution: Distribution = Depends(get_distribution_by_host),
) -> TypeIDType:
    """
    Right before we pass off the user to Stripe, we save all order information.

    This can happen multiple times if there is a form submission error with Stripe.

    This pending step is in place largely because many payment methods require a redirect to a confirmation page,
    so we assume we'll always be redirected.

    The database schema ensures duplicate stripe checkout session ids never happen.
    """


    # let's validate the stripe checkout session id is real
    stripe_session = stripe_client.checkout.sessions.retrieve(
        data.stripe_checkout_session_id
    )

    if stripe_session.status != "open":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Your checkout session has expired. Please refresh the page and try again.",
        )

    order = Order.one_or_none(
        stripe_checkout_session_id=data.stripe_checkout_session_id
    )

    if order:
        order.email = data.email
        # ...and other fields...
        order.save()
    else:
        order = Order(
            stripe_checkout_session_id=data.stripe_checkout_session_id,
            email=data.email,
        ).save()

    return order.id


@screening_api_app.get("/complete")
def complete_ticket_purchase(
    request: Request,
    session_id: str = Query(),
):
    stripe_session = stripe_client.checkout.sessions.retrieve(session_id)

    if stripe_session.status != "complete":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    order = Order.one(stripe_checkout_session_id=session_id)

    order.status = OrderState.paid
    order.save()

    redirect_url = f"{origin_url}/screening/{order.screening_id}/confirmation/{session_id}"
    return RedirectResponse(url=redirect_url)


@screening_api_app.get("/confirmation")
def ticket_purchase_status(
    request: Request,
    stripe_checkout_session_id: str = Query(),
    screening_id: TypeIDType = Query(),
) -> str:
    stripe_client = distribution.stripe_client()
    stripe_session = stripe_client.checkout.sessions.retrieve(
        stripe_checkout_session_id
    )

    if stripe_session.status != "complete":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Checkout is not complete",
        )

    order = Order.one(stripe_checkout_session_id=stripe_checkout_session_id)
    return order.id


public_api_app.include_router(screening_api_app)
```
