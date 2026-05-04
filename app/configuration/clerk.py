from clerk_backend_api import Clerk

from app.env import env
from app.environments import is_debug_logging

CLERK_PRIVATE_KEY = env.str("CLERK_PRIVATE_KEY")

# we lose the typing with this approach, but
clerk_kwargs = {}

if is_debug_logging():
    import logging

    clerk_kwargs["debug_logger"] = logging.getLogger("app.clerk")

clerk = Clerk(bearer_auth=CLERK_PRIVATE_KEY, **clerk_kwargs)
