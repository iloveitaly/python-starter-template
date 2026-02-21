from clerk_backend_api import Clerk

from app.env import env

CLERK_PRIVATE_KEY = env.str("CLERK_PRIVATE_KEY")

clerk = Clerk(
    bearer_auth=CLERK_PRIVATE_KEY,
)

# TODO add debug logger configuration
