import posthog
from posthog import contexts
from starlette.requests import Request
from structlog_config import fastapi_access_logger


def _identify_posthog(request: Request) -> None:
    # clerk_id matches the uuid the frontend uses, so FE and BE events merge
    user = getattr(request.state, "user", None)
    if user is not None and getattr(user, "clerk_id", None):
        posthog.identify_context(user.clerk_id)

    # header wins when both are set, same as applying tags after identity
    if distinct_id := request.headers.get("X-Posthog-Distinct-Id"):
        contexts.identify_context(distinct_id)

    if session_id := request.headers.get("X-Posthog-Session-Id"):
        contexts.set_context_session(session_id)


def _tag_posthog_request(request: Request) -> None:
    tags = {}

    if absolute_url := str(request.url):
        tags["$current_url"] = absolute_url

    if request.method:
        tags["$request_method"] = request.method

    if request.url.path:
        tags["$request_path"] = request.url.path
        # the js SDK uses this param, I suspect $request_path is incorrect
        tags["$pathname"] = request.url.path

    if request_ip := fastapi_access_logger.client_ip_from_request(request):
        # django uses $ip_address, but posthog web library uses $ip
        tags["$ip"] = request_ip

    # although absolute_url contains the host, we must set it separately
    if request.url.hostname:
        tags["$host"] = request.url.hostname

    for key, value in tags.items():
        contexts.tag(key, value)


async def inject_posthog_context(request: Request):
    """
    One context for this request so identity and tags land on the same events.

    PostHog does not allow email here. Set that in the JS library.
    `capture` posts asynchronously, so this does not block the request.

    https://posthog.com/docs/getting-started/identify-users
    """

    with posthog.new_context():
        _identify_posthog(request)
        _tag_posthog_request(request)
        yield
