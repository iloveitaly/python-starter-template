from stripe import StripeClient

from app.env import env


def stripe_client() -> StripeClient:
    "Client for example payment routes. STRIPE_SECRET_KEY is read on use, not import"

    return StripeClient(env.str("STRIPE_SECRET_KEY"))
