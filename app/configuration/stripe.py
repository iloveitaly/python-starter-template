from stripe import StripeClient

from app.env import env

STRIPE_SECRET_KEY = env.str("STRIPE_SECRET_KEY")

stripe_client = StripeClient(STRIPE_SECRET_KEY)
