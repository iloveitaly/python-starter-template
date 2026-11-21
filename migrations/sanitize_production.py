"""
Make a production DB dump safe for local development by:

1. Randomizing all stored Stripe checkout/payment IDs across the database
2. ... other application specific logic

Notes:

- Must be executed directly and must not be imported.
- Refuses to run in production or staging.
"""

if __name__ != "__main__":
    raise RuntimeError(
        "This module should only be executed directly and should not be imported."
    )

from app.environments import is_production, is_staging

# do not allow running in staging or production
if is_production() or is_staging():
    raise RuntimeError("sanitize_production.py must never run in production or staging")


from activemodel.session_manager import global_session


def randomize_stripe_checkout_and_payment_ids() -> None:
    """Randomize stored Stripe IDs so a production dump does not leak them.

    This template has no model with a Stripe ID, so there is nothing to update.
    """


def main() -> None:
    with global_session():
        randomize_stripe_checkout_and_payment_ids()


if __name__ == "__main__":
    main()
