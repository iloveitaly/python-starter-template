from operator import attrgetter

import stripe
from fastapi import HTTPException
from starlette import status


def extract_payment_intent_id_from_client_secret(client_secret_id: str) -> str:
    """
    Extracts the payment_intent_id from a Stripe client_secret_id. Designed for a fastapi route which expects a valid client_secret_id.

    >>> extract_payment_intent_id_from_client_secret("pi_3RPofKPNRRX3VZhd0CHUAjEi_secret_aRC74awl3qM01aWWqSDDF8t1r")
    'pi_3RPofKPNRRX3VZhd0CHUAjEi'
    """

    # TODO need to add details to the exception

    if not client_secret_id or "_secret" not in client_secret_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST)

    payment_intent_id = client_secret_id.split("_secret")[0]
    if not payment_intent_id.startswith("pi_"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST)

    return payment_intent_id


def extract_checkout_session_id_from_client_secret(client_secret_id: str) -> str:
    """
    Example:
    >>> extract_checkout_session_id_from_client_secret("cs_test_a1tQWKwHJ9fMYVL2TjkDDqX2qvvnKnI3zb5dw3exS1wb0TXvEjwVxXKmzo_secret_fidwbEhqYWAnPydmcHZxamgneCUl")
    'cs_test_a1tQWKwHJ9fMYVL2TjkDDqX2qvvnKnI3zb5dw3exS1wb0TXvEjwVxXKmzo'
    """
    if not client_secret_id or "_secret" not in client_secret_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST)

    session_id = client_secret_id.split("_secret")[0]
    if not session_id.startswith("cs_"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST)

    return session_id


ALLOWED_STRIPE_TYPES = {
    "customers",
    "invoice_items",
    "invoices",
    "charges",
    "refunds",
    "disputes",
    "transfers",
    "plans",
    "coupons",
    "orders",
    "skus",
    "payment_intents",
    "balance_transactions",
    "subscription_items",
    "products",
    "setup_intents",
    "payment_methods",
    "checkout_sessions",
}


def whitelist_stripe_service(service_string: str) -> str:
    if service_string in ALLOWED_STRIPE_TYPES:
        return service_string
    raise ValueError(f"invalid stripe service: {service_string}")


def get_stripe_type_from_id(
    stripe_object_id: str, raise_on_missing: bool = True
) -> str | None:
    if stripe_object_id.startswith(("re_", "pyr_")):
        return "refunds"
    elif stripe_object_id.startswith(("tr_", "po_")):
        return "transfers"
    elif stripe_object_id.startswith(("ch_", "py_")):
        return "charges"
    elif stripe_object_id.startswith(("dp_", "pdp_", "du_")):
        return "disputes"
    elif stripe_object_id.startswith("or_"):
        return "orders"
    elif stripe_object_id.startswith("in_"):
        return "invoices"
    elif stripe_object_id.startswith("cus_"):
        return "customers"
    elif stripe_object_id.startswith("txn_"):
        return "balance_transactions"
    elif stripe_object_id.startswith("ii_"):
        return "invoice_items"
    elif stripe_object_id.startswith("si_"):
        return "subscription_items"
    elif stripe_object_id.startswith("plan_"):
        return "plans"
    elif stripe_object_id.startswith("prod_"):
        return "products"
    elif stripe_object_id.startswith("sku_"):
        return "skus"
    elif stripe_object_id.startswith("seti_"):
        return "setup_intents"
    elif stripe_object_id.startswith("pi_"):
        return "payment_intents"
    elif stripe_object_id.startswith("pm_"):
        return "payment_methods"
    elif stripe_object_id.startswith("cs_"):
        return "checkout.sessions"
    else:
        if raise_on_missing:
            raise ValueError(f"unknown stripe id: {stripe_object_id}")
        return None


def stripe_retrieve(stripe_object_id: str, client: stripe.StripeClient):
    assert isinstance(client, stripe.StripeClient)

    stripe_type = get_stripe_type_from_id(stripe_object_id)
    if stripe_type is None:
        raise ValueError(f"Cannot retrieve for id: {stripe_object_id}")

    # Resolve dotted attributes like "checkout.sessions" or single-level names
    return attrgetter(stripe_type)(client).retrieve(stripe_object_id)


def payment_intent_is_disputed(
    client: stripe.StripeClient, payment_intent_id: str
) -> bool:
    """
    Returns True if any charge for the PaymentIntent has an active dispute.
    """
    for charge in client.charges.list(
        params={"payment_intent": payment_intent_id}
    ).auto_paging_iter():
        if charge.disputed:
            return True

    return False
