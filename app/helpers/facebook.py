"""
Facebook/Meta tracking helpers

- Surprisingly, the pixel endpoint is pretty slow. Can be 200-400ms per request. Throw this in a background thread
  when possible.

TODO

- disable option for local tests? Is this needed with how facebook works?
"""

import time
from typing import Literal

import phonenumbers
import sentry_sdk
from capi_param_builder import ParamBuilder
from facebook_business.adobjects.serverside.action_source import ActionSource
from facebook_business.adobjects.serverside.custom_data import CustomData
from facebook_business.adobjects.serverside.event import Event
from facebook_business.adobjects.serverside.event_request import EventRequest
from facebook_business.adobjects.serverside.user_data import UserData
from facebook_business.api import FacebookAdsApi
from fastapi import BackgroundTasks, Request
from phonenumbers import NumberParseException, PhoneNumberFormat
from structlog_config.fastapi_access_logger import client_ip_from_request

from app import log
from app.env import env

META_PIXEL_ID = env.str("META_PIXEL_ID")
META_PIXEL_KEY = env.str("META_PIXEL_KEY")

# tests can set this without relying on an environment variable
TEST_EVENT_CODE_OVERRIDE: str | None = None


def set_test_event_code(code: str | None) -> None:
    """Set the Meta test event code for tests without using an env var."""
    global TEST_EVENT_CODE_OVERRIDE
    TEST_EVENT_CODE_OVERRIDE = code


FBP_COOKIE_NAME = "_fbp"
"Facebook Browser ID cookie - tracks user across sessions"

FBC_COOKIE_NAME = "_fbc"
"Facebook Click ID cookie - tracks clicks from Facebook ads"

FBP_QUERY_PARAM = "fbp"
"Query parameter for Facebook Browser ID"

FBC_QUERY_PARAM = "fbc"
"Query parameter for Facebook Click ID"

FBCLID_QUERY_PARAM = "fbclid"
"Query parameter for Facebook Click ID from ad clicks"

USER_AGENT_HEADER = "user-agent"
"HTTP header containing user agent string"

# casefolded substrings, so `healthcheck` also covers ELB-HealthChecker and Cloudflare-Healthchecks
_MONITORING_USER_AGENT_MARKERS = (
    "uptime-kuma",
    "uptimerobot",
    "pingdom",
    "kube-probe",
    "kubelet",
    "curl/",
    "wget",
    "googlehc",
    "amazon-route53-health-check",
    "better uptime",
    "sentryuptimebot",
    "healthcheck",
)

MetaEventName = Literal[
    # should be used if we don't have a content ID and/or price
    "PageView",
    # for viewing a specific piece of content, probably for in-page interactions
    "ViewContent",
    "Search",
    "AddToCart",
    "AddToWishlist",
    "InitiateCheckout",
    "AddPaymentInfo",
    "Purchase",
    "Lead",
    "CompleteRegistration",
    "Contact",
    "CustomizeProduct",
    "Donate",
    "FindLocation",
    "Schedule",
    "StartTrial",
    "SubmitApplication",
    "Subscribe",
]


def _is_monitoring_user_agent(user_agent: str | None) -> bool:
    """
    True for uptime probes and other synthetic HTTP clients.

    A poller hits public routes on a timer and carries no click id, browser id,
    or hashed identifiers. Sending that as a conversion adds a zero-quality
    event and an outbound call to graph.facebook.com on every poll.

    Absence of the header is not enough to skip: some real clients strip it.
    """

    if not user_agent:
        return False

    folded = user_agent.casefold()
    return any(marker in folded for marker in _MONITORING_USER_AGENT_MARKERS)


def _normalize_phone(phone: str, region: str | None) -> str | None:
    """
    E.164 without the leading `+`, which is the shape Meta hashes phone numbers in.

    `region` is only consulted for numbers typed without a `+`, so it decides how a bare
    national number is read: `22 622 15 00` is a real Warsaw line under `PL` and a bogus
    +1 under `US`. Pass the buyer's country so non-US locals aren't mangled into an
    invalid +1 and dropped below.

    Parsing succeeding is not enough to send: it only means the string was number-shaped.
    `555-555-5555`, `1234567890` and `00000` all parse and none of them are real numbers,
    so `is_valid_number` is what keeps unmatchable hashes out of the `ph` key.
    """

    try:
        parsed = phonenumbers.parse(phone, region)
    except NumberParseException:
        log.warning("phone unparseable, omitting from meta event", region=region)
        return None

    if not phonenumbers.is_valid_number(parsed):
        log.warning("phone invalid, omitting from meta event", region=region)
        return None

    return phonenumbers.format_number(parsed, PhoneNumberFormat.E164).lstrip("+")


def _split_full_name(full_name: str) -> tuple[str | None, str | None]:
    parts = [p for p in full_name.strip().split() if p]
    if not parts:
        return None, None
    if len(parts) == 1:
        return parts[0], None

    return parts[0], parts[-1]


def _resolve_fbp(request: Request) -> str | None:
    "Facebook Browser ID, preferring an explicit query param over the cookie"

    if fbp := request.query_params.get(FBP_QUERY_PARAM):
        cookie_fbp = request.cookies.get(FBP_COOKIE_NAME)

        if cookie_fbp is None:
            log.warning("fbp cookie missing while query param present")
        elif cookie_fbp == "":
            log.warning("fbp cookie empty while query param present")
        elif cookie_fbp != fbp:
            log.warning(
                "fbp query param and cookie mismatch",
                query_value=fbp,
                cookie_value=cookie_fbp,
            )

        log.debug("fbp resolved", source="query")
        return fbp

    if fbp := request.cookies.get(FBP_COOKIE_NAME):
        log.debug("fbp resolved", source="cookie")
        return fbp

    log.debug("fbp not resolved")
    return None


def resolve_fbc(
    request: Request, tracking_params: dict[str, str] | None = None
) -> str | None:
    """
    Facebook Click ID in the `fbc` wire format, derived from the request.

    Meta (and PostHog's Meta Ads destination) want the fully-formed value rather than a
    bare `fbclid`, since a raw click ID has to be paired with a click time and anything
    reconstructing it later can only guess `now()`. Resolving it here, at the request
    that actually carries the ad click, keeps that timestamp honest.

    `tracking_params` covers the requests the ad click cannot ride on by itself: an XHR
    posted from a page whose *URL* carries the click, with the params forwarded in the
    body by `trackingParamsFromSearch()`. Without it those requests fall through to the
    `_fbc` cookie, which does not exist when the Meta pixel is blocked.
    """

    params = {**request.query_params, **(tracking_params or {})}

    if fbc := params.get(FBC_QUERY_PARAM):
        cookie_fbc = request.cookies.get(FBC_COOKIE_NAME)

        if cookie_fbc is None:
            log.warning("fbc cookie missing while query param present")
        elif cookie_fbc == "":
            log.warning("fbc cookie empty while query param present")
        elif cookie_fbc != fbc:
            log.warning(
                "fbc query param and cookie mismatch",
                query_value=fbc,
                cookie_value=cookie_fbc,
            )

        log.debug("fbc resolved", source="query")
        return fbc

    if params.get(FBCLID_QUERY_PARAM):
        # ParamBuilder derives the subdomain index, millisecond timestamp, and Meta version appendix
        builder = ParamBuilder()
        builder.process_request(
            host=request.headers.get("host") or "",
            queries={key: [value] for key, value in params.items()},
            cookies=dict(request.cookies),
        )

        if fbc := builder.get_fbc():
            log.debug("fbc resolved", source="fbclid")
            return fbc

    if fbc := request.cookies.get(FBC_COOKIE_NAME):
        log.debug("fbc resolved", source="cookie")
        return fbc

    log.debug("fbc not resolved")
    return None


def build_meta_user_data(
    request: Request,
    *,
    email: str | None = None,
    phone: str | None = None,
    city: str | None = None,
    state: str | None = None,
    zip_code: str | None = None,
    country: str | None = None,
    first_name: str | None = None,
    last_name: str | None = None,
    full_name: str | None = None,
    fbc: str | None = None,
) -> UserData:
    fbp = _resolve_fbp(request)
    fbc = fbc or resolve_fbc(request)

    if full_name and not (first_name or last_name):
        split_first, split_last = _split_full_name(full_name)
        first_name = first_name or split_first
        last_name = last_name or split_last

    if phone is not None:
        # phonenumbers needs an uppercase region code; default to US when none is given
        phone = _normalize_phone(phone, country.upper() if country else "US")

    # constructor args are mistyped as required `str` in the SDK's stubs, so assign via
    # the correctly-typed property setters instead
    user_data = UserData()
    user_data.email = email
    user_data.phone = phone
    user_data.first_name = first_name
    user_data.last_name = last_name
    user_data.city = city
    user_data.state = state
    user_data.zip_code = zip_code
    user_data.country_code = country
    user_data.fbp = fbp
    user_data.fbc = fbc
    user_data.client_ip_address = client_ip_from_request(request)
    user_data.client_user_agent = request.headers.get(USER_AGENT_HEADER)
    return user_data


def send_conversion_event(
    *,
    event_name: MetaEventName,
    request: Request,
    value_in_cents: int | None = None,
    currency: str = "USD",
    email: str | None = None,
    phone: str | None = None,
    city: str | None = None,
    state: str | None = None,
    zip_code: str | None = None,
    country: str | None = None,
    first_name: str | None = None,
    last_name: str | None = None,
    full_name: str | None = None,
    event_id: str | None = None,
    fbc: str | None = None,
    background_tasks: BackgroundTasks | None = None,
) -> None:
    """
    Build and send a Meta Conversions API event.

    Sends async via `background_tasks` when provided, since the pixel endpoint can take
    200-400ms and that cost shouldn't land on the caller's request. Failures are swallowed
    by `_send_facebook_event`, so this never fails the request it rides on.

    Monitoring clients are dropped before an event is built. A match key on the
    request does not override that: the client is still the probe.

    When fbc is omitted, it is resolved from the request’s query parameters, then the _fbc cookie.
    Landing-page parameters must be explicitly forwarded to API requests.
    This fallback does not inspect the request body. Pass fbc when it was already captured earlier.
    """
    user_agent = request.headers.get(USER_AGENT_HEADER)
    if _is_monitoring_user_agent(user_agent):
        log.debug(
            "skipping meta event for monitoring client",
            event_name=event_name,
            user_agent=user_agent,
        )
        return

    custom_data = None
    if value_in_cents is not None:
        custom_data = CustomData(
            value=round(value_in_cents / 100, 2),
            currency=currency,
        )

    event = Event(event_name=event_name, event_time=int(time.time()))
    event.action_source = ActionSource.WEBSITE
    event.event_source_url = str(request.url)
    event.user_data = build_meta_user_data(
        request,
        email=email,
        phone=phone,
        city=city,
        state=state,
        zip_code=zip_code,
        country=country,
        first_name=first_name,
        last_name=last_name,
        full_name=full_name,
        fbc=fbc,
    )
    if custom_data is not None:
        event.custom_data = custom_data
    event.event_id = event_id

    if background_tasks:
        background_tasks.add_task(_send_facebook_event, event, TEST_EVENT_CODE_OVERRIDE)
    else:
        _send_facebook_event(event, TEST_EVENT_CODE_OVERRIDE)


def _send_facebook_event(event: Event, test_event_code: str | None = None) -> None:
    try:
        FacebookAdsApi.init(
            access_token=META_PIXEL_KEY,
            # Without this, Facebook overrides sys.excepthook and sends exception data to its servers.
            crash_log=False,
        )
        event_request = EventRequest(
            pixel_id=META_PIXEL_ID,
            events=[event],
        )
        if test_event_code:
            event_request.test_event_code = test_event_code
        event_request.execute()
    except Exception:  # noqa: BLE001
        # structlog writes straight to stdout, so nothing here reaches Sentry on its own
        sentry_sdk.capture_exception()
        log.exception(
            "facebook pixel event send failed",
            event_name=event.event_name,
        )
