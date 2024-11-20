from clerk_backend_api import Clerk
from decouple import config

CLERK_PRIVATE_KEY = config("CLERK_PRIVATE_KEY", cast=str)

clerk = Clerk(
    bearer_auth=CLERK_PRIVATE_KEY,
)

# TODO add debug logger configuration
