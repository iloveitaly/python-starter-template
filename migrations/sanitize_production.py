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


from app import log

from activemodel.session_manager import get_session, global_session


def randomize_stripe_checkout_and_payment_ids() -> None:
    """Randomize stored Stripe IDs to avoid leaking production identifiers.

    - TicketReservationOrder.stripe_checkout_session_id
    """

    # the template does not have a model with a stripe ID
    return

    with get_session() as session:
        # session.exec(
        #     TicketReservationOrder.__table__.update().values(
        #         {
        #             "stripe_checkout_session_id": literal("cs_test_")
        #             + func.base32_encode(func.gen_random_uuid()),
        #             "stripe_payment_intent_id": literal("pi_")
        #             + func.base32_encode(func.gen_random_uuid()),
        #         }
        #     )
        # )

        session.commit()

    log.info("randomized stripe ids")


def main() -> None:
    with global_session():
        randomize_stripe_checkout_and_payment_ids()


if __name__ == "__main__":
    main()
