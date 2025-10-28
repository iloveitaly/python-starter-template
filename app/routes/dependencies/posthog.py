import posthog
from posthog import contexts
from starlette.requests import Request
from structlog_config import fastapi_access_logger


async def inject_posthog_identity(request: Request):
    """
    Attaching an identity UUID:

    1. Eliminates the need for us to do this on each call
    2. Allows posthog to merge FE events into the same user[0]

    Some notes about posthog:

    - Does not allow email, and other additional properties to be set. This must be set within the JS library.
    - `capture` runs all POSTs async, so we don't have to worry about blocking the request.

    [0]
    https://posthog.com/docs/getting-started/identify-users

    > If two users have the same distinct ID, their data is merged and they are considered one user in PostHog.
    """

    with posthog.new_context(capture_exceptions=False):
        # by using clerk_id, we can easily use the same UUID on frontend events
        posthog.identify_context(request.state.user.clerk_id)
        yield


async def inject_posthog_tags(request: Request):
    """
    Inject some common tags into posthog events for this request. This is helpful for linking frontend events to backend events.

    The Django implementation pulls a lot of data from the request. However, this data should already be in place from the frontend
    library. If it's not, something else is wrong and we shouldn't hack around it by including more data here.

    Instead, let's primary just tag the distinct_id and session_id from the request headers. These are injected in all HeyAPI
    requests, but are *not* guaranteed to be present on all requests.

    https://github.com/PostHog/posthog-python/blob/master/posthog/integrations/django.py
    """

    # by default, there is not a context, so we must define one
    # `capture_exceptions=False` https://github.com/PostHog/posthog-python/issues/353
    with posthog.new_context(capture_exceptions=False):
        # intentionally overwrite any other session or distinct id set previously
        # it's up to the user to add dependencies in the correct order
        if distinct_id := request.headers.get("X-Posthog-Distinct-Id"):
            contexts.identify_context(distinct_id)

        if session_id := request.headers.get("X-Posthog-Session-Id"):
            contexts.set_context_session(session_id)

        tags = {}

        if absolute_url := str(request.url):
            tags["$current_url"] = absolute_url

        if request.method:
            tags["$request_method"] = request.method

        if request.url.path:
            tags["$request_path"] = request.url.path

        if request_ip := fastapi_access_logger.client_ip_from_request(request):
            # django uses $ip_address, but posthog web library uses $ip
            tags["$ip"] = request_ip

        # although absolute_url contains the host, we must set it separately
        if request.url.hostname:
            tags["$host"] = request.url.hostname

        for k, v in tags.items():
            contexts.tag(k, v)

        yield
