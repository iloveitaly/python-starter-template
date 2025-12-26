"""
Facebook/Meta tracking helpers

- Surprisingly, the pixel endpoint is pretty slow. Can be 200-400ms per request. Throw this in a background thread
  when possible.

TODO

- disable option for local tests? Is this needed with how facebook works?
"""

import hashlib
import re
import time
from typing import Literal

from decouple import config
from facebook_business.adobjects.adspixel import AdsPixel
from facebook_business.api import FacebookAdsApi
from fastapi import BackgroundTasks, Request
from pydantic import BaseModel
from structlog_config.fastapi_access_logger import client_ip_from_request

from app import log

META_PIXEL_ID = config("META_PIXEL_ID", cast=str)
META_PIXEL_KEY = config("META_PIXEL_KEY", cast=str)

# tests can set this without relying on an environment variable
TEST_EVENT_CODE_OVERRIDE: str | None = None


def set_test_event_code(code: str | None) -> None:
    """Set the Meta test event code for tests without using an env var."""
    global TEST_EVENT_CODE_OVERRIDE
    TEST_EVENT_CODE_OVERRIDE = code


API_VERSION = "v20.0"

# request/cookie parameter names
FBP_COOKIE_NAME = "_fbp"
"""Facebook Browser ID cookie - tracks user across sessions"""

FBC_COOKIE_NAME = "_fbc"
"""Facebook Click ID cookie - tracks clicks from Facebook ads"""

FBP_QUERY_PARAM = "fbp"
"""Query parameter for Facebook Browser ID"""

FBC_QUERY_PARAM = "fbc"
"""Query parameter for Facebook Click ID"""

FBCLID_QUERY_PARAM = "fbclid"
"""Query parameter for Facebook Click ID from ad clicks"""

USER_AGENT_HEADER = "user-agent"
"""HTTP header containing user agent string"""

# event payload constants
ACTION_SOURCE_WEBSITE = "website"


class MetaUserData(BaseModel):
    fbp: str | None = None
    fbc: str | None = None
    client_ip_address: str | None = None
    client_user_agent: str | None = None
    # hashed identifiers per Meta CAPI spec
    em: str | None = None
    ph: str | None = None
    fn: str | None = None
    ln: str | None = None
    ct: str | None = None
    st: str | None = None
    zp: str | None = None
    country: str | None = None

    def as_sdk_dict(self) -> dict:
        return self.model_dump(exclude_none=True)


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


def get_facebook_pixel() -> AdsPixel:
    FacebookAdsApi.init(
        access_token=META_PIXEL_KEY,
        api_version=API_VERSION,
        # this is crazy: without this, facebook overrides sys.excepthook AND sends exception data to their servers
        crash_log=False,
    )
    return AdsPixel(META_PIXEL_ID)


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _normalize_phone(phone: str) -> str:
    # keep digits only
    digits = re.sub(r"\D", "", phone)
    # best-effort: if US 10-digit, prefix country code 1
    if len(digits) == 10:
        return f"1{digits}"
    return digits


def _normalize_name(value: str) -> str:
    return value.strip().lower()


def _normalize_city(value: str) -> str:
    return value.strip().lower()


def _normalize_state(value: str) -> str:
    return value.strip().lower()


def _normalize_zip(value: str) -> str:
    return value.strip().lower()


def _normalize_country(value: str) -> str:
    return value.strip().lower()


def _split_full_name(full_name: str) -> tuple[str | None, str | None]:
    parts = [p for p in full_name.strip().split() if p]
    if not parts:
        return None, None
    if len(parts) == 1:
        return parts[0], None
    return parts[0], parts[-1]


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
) -> MetaUserData:
    query_params = request.query_params

    # fbp: prefer explicit query param, then cookie
    if fbp := query_params.get(FBP_QUERY_PARAM):
        fbp_source = "query"
    elif fbp := request.cookies.get(FBP_COOKIE_NAME):
        fbp_source = "cookie"
    else:
        fbp_source = None

    if fbp_source == "query":
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

    # fbc: prefer explicit query param, then construct from fbclid, then cookie
    if fbc := query_params.get(FBC_QUERY_PARAM):
        fbc_source = "query"
    elif fbclid := query_params.get(FBCLID_QUERY_PARAM):
        # TODO explain where this recommended format comes from
        # recommended format when derived from fbclid
        fbc = f"fb.1.{int(time.time())}.{fbclid}"
        fbc_source = "fbclid"
    elif fbc := request.cookies.get(FBC_COOKIE_NAME):
        fbc_source = "cookie"
    else:
        fbc = None
        fbc_source = None

    if fbc_source == "query":
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

    if fbp_source:
        log.debug("fbp resolved", source=fbp_source)
    else:
        log.debug("fbp not resolved")

    if fbc_source:
        log.debug("fbc resolved", source=fbc_source)
    else:
        log.debug("fbc not resolved")

    em_hashed = _sha256(_normalize_email(email)) if email else None
    ph_hashed = _sha256(_normalize_phone(phone)) if phone else None

    if full_name and not (first_name or last_name):
        split_first, split_last = _split_full_name(full_name)
        first_name = first_name or split_first
        last_name = last_name or split_last

    fn_hashed = _sha256(_normalize_name(first_name)) if first_name else None
    ln_hashed = _sha256(_normalize_name(last_name)) if last_name else None
    ct_hashed = _sha256(_normalize_city(city)) if city else None
    st_hashed = _sha256(_normalize_state(state)) if state else None
    zp_hashed = _sha256(_normalize_zip(zip_code)) if zip_code else None
    country_hashed = _sha256(_normalize_country(country)) if country else None

    return MetaUserData(
        fbp=fbp,
        fbc=fbc,
        client_ip_address=client_ip_from_request(request),
        client_user_agent=request.headers.get(USER_AGENT_HEADER),
        em=em_hashed,
        ph=ph_hashed,
        fn=fn_hashed,
        ln=ln_hashed,
        ct=ct_hashed,
        st=st_hashed,
        zp=zp_hashed,
        country=country_hashed,
    )


def build_conversion_event_payload(
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
    background_tasks: BackgroundTasks | None = None,
) -> dict:
    """Build a Facebook Pixel event payload.

    https://developers.facebook.com/docs/marketing-api/conversions-api/parameters/server-event"""
    # derive values that used to be parameters
    event_time = int(time.time())
    event_source_url = str(request.url)

    custom_data = None
    if value_in_cents is not None:
        custom_data = {"value": round(value_in_cents / 100, 2), "currency": currency}

    payload: dict = {
        "data": [
            {
                "event_name": event_name,
                "event_time": event_time,
                "action_source": ACTION_SOURCE_WEBSITE,
                "event_source_url": event_source_url,
                "user_data": build_meta_user_data(
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
                ).as_sdk_dict(),
                "custom_data": custom_data,
                # order id, or other unique identifier for deduplication
                "event_id": event_id,
            }
        ]
    }

    # include test event code only when set by tests
    if TEST_EVENT_CODE_OVERRIDE:
        payload["test_event_code"] = TEST_EVENT_CODE_OVERRIDE

    # Send async if background_tasks provided, otherwise sync
    if background_tasks:
        background_tasks.add_task(_send_facebook_event, payload, event_name)
    else:
        _send_facebook_event(payload, event_name)

    return payload


def _send_facebook_event(payload: dict, event_name: str) -> None:
    """Send event to Facebook."""
    try:
        pixel = get_facebook_pixel()
        pixel.create_event(params=payload)
    except Exception as e:  # noqa: BLE001
        log.exception(
            "facebook pixel event send failed",
            error=str(e),
            event_name=payload["data"][0]["event_name"],
        )
