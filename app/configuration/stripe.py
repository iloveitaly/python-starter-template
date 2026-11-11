from stripe import StripeClient

from app.env import env

STRIPE_SECRET_KEY = env.str("STRIPE_SECRET_KEY")


def stripe_client() -> StripeClient:
    return StripeClient(STRIPE_SECRET_KEY)
