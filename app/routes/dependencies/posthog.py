import posthog
from starlette.requests import Request


async def inject_posthog_identity(request: Request):
    """
    Attaching an identity UUID:

    1. Eliminates the need for us to do this on each call
    2. Allows posthog to merge FE events into the same user

    Some notes about posthog:

    - Does not allow email, and other additional properties to be set. This must be set within the JS library.
    - `capture` runs all POSTs async
    """

    with posthog.new_context():
        # by using clerk_id, we can easily use the same UUID on frontend events
        posthog.identify_context(request.state.user.clerk_id)
        yield
