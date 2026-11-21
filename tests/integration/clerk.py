"""
Helpers to avoid hitting Captchas when testing.

Adapted from:

- https://github.com/clerk/javascript/blob/main/packages/testing/src/playwright/setupClerkTestingToken.ts
- https://github.com/clerk/javascript/tree/main/packages/testing/src/playwright

Update prompt:

> https://github.com/clerk/javascript/commits/main/packages/testing/src/playwright
> I'd like to inspect the history of this package. Clone it to tmp/ and inspect the changes on This folder over the last four months. Adapt any changes in the JavaScript to the clerk.py that I've referenced.

Usage:

>>> def test_signup(server, page: Page) -> None:
>>>    setup_clerk_testing_token(page)

Attempting to upstream at: https://github.com/clerk/clerk-sdk-python/pull/65/files
"""

import logging
import os
import random
import re
import time
from dataclasses import dataclass
from urllib.parse import parse_qs, urlencode, urlparse
from weakref import WeakSet

import httpx
from clerk_backend_api import Clerk
from clerk_backend_api.models.clerkbaseerror import ClerkBaseError
from playwright.sync_api import APIResponse, BrowserContext, Page, Request, Route
from whenever import Instant

from tests.utils import base64_decode

logger = logging.getLogger(__name__)


@dataclass
class SetupClerkTestingTokenOptions:
    frontend_api_url: str | None = None


TESTING_TOKEN_PARAM = "__clerk_testing_token"  # nosec B105

PUBLISHABLE_KEY_LIVE_PREFIX = "pk_live_"
PUBLISHABLE_KEY_TEST_PREFIX = "pk_test_"

# Matches publishable frontend API keys (e.g. foo-bar-13.clerk.accounts.dev)
PUBLISHABLE_FRONTEND_API_DEV_REGEX = (
    r"^(([a-z]+)-){2}([0-9]{1,2})\.clerk\.accounts([a-z.]*)(dev|com)$"
)

RETRYABLE_ROUTE_STATUS_CODES = frozenset({429, 502, 503, 504})
MAX_ROUTE_RETRIES = 3
ROUTE_BASE_DELAY_MS = 500
ROUTE_JITTER_MAX_MS = 250

RETRYABLE_API_STATUS_CODES = frozenset({408, 429, 500, 502, 503, 504})
MAX_API_RETRIES = 5
API_BASE_DELAY_MS = 1000
API_JITTER_MAX_MS = 500
API_MAX_RETRY_DELAY_MS = 30_000

_setup_contexts: WeakSet[BrowserContext] = WeakSet()


def clerk_test_email() -> str:
    """
    Unique email every time can that be used to login to clerk using test codes.

    https://clerk.com/docs/testing/test-emails-and-phones

    Use verification code 424242.
    """

    return f"test-{Instant.now().timestamp()}+clerk_test@example.com"


def clerk_login_and_verify(page: Page, email: str) -> None:
    """
    Login to Clerk and verify the email.
    """
    page.get_by_label("Email address").fill(email)
    page.get_by_role("button", name="Continue", exact=True).click()
    page.get_by_label("Enter verification code", exact=True).press_sequentially(
        # slowly type the verification code, it's one single input
        "424242",
        delay=100,
    )
    # when the verification code is filled, the button will automatically be clicked


@dataclass
class PublishableKey:
    instance_type: str
    frontend_api: str


def is_publishable_key(key: str) -> bool:
    if not key:
        return False

    has_valid_prefix = key.startswith(
        (PUBLISHABLE_KEY_LIVE_PREFIX, PUBLISHABLE_KEY_TEST_PREFIX)
    )

    has_valid_postfix = (
        base64_decode(key.split("_")[2] if len(key.split("_")) > 2 else "")
        .decode("utf-8")
        .endswith("$")
    )

    return has_valid_prefix and has_valid_postfix


def parse_publishable_key(
    key: str | None,
    domain: str | None = None,
    proxy_url: str | None = None,
) -> PublishableKey | None:
    if not key or not is_publishable_key(key):
        return None

    instance_type = (
        "development" if key.startswith(PUBLISHABLE_KEY_TEST_PREFIX) else "production"
    )

    frontend_api = base64_decode(key.split("_")[2]).decode("utf-8")[:-1]

    if proxy_url:
        frontend_api = proxy_url
    elif instance_type != "development" and domain:
        frontend_api = f"clerk.{domain}"

    return PublishableKey(instance_type=instance_type, frontend_api=frontend_api)


def _resolve_frontend_api_url(frontend_api_url: str | None = None) -> str:
    if not frontend_api_url:
        frontend_api_url = os.environ.get("CLERK_FAPI_URL") or os.environ.get(
            "CLERK_FAPI"
        )

    if (
        not frontend_api_url
        and (clerk_publishable_key := os.environ.get("CLERK_PUBLISHABLE_KEY"))
        and (parsed_publishable_key := parse_publishable_key(clerk_publishable_key))
    ):
        # the publishable key non-static component is base64 encoded version of the frontend api url
        frontend_api_url = parsed_publishable_key.frontend_api

    if not frontend_api_url:
        raise ValueError("Frontend API URL or valid publishable key is required")

    return frontend_api_url


def _build_api_url_pattern(frontend_api_url: str) -> re.Pattern[str]:
    return re.compile(rf"^https://{re.escape(frontend_api_url)}/v1/.*?(\?.*)?$")


def _compute_backoff_delay_ms(
    attempt: int, base_delay_ms: int, jitter_max_ms: int
) -> float:
    return base_delay_ms * (2**attempt) + random.uniform(0, jitter_max_ms)  # nosec B311


def _format_response_diagnostics(response: APIResponse) -> str:
    """Collect best-effort diagnostics from an exhausted FAPI response."""
    try:
        headers = response.headers
        body_preview = response.text()[:500]
        return (
            f"\n  cf-ray: {headers.get('cf-ray', 'n/a')}, "
            f"retry-after: {headers.get('retry-after', 'n/a')}, "
            f"content-type: {headers.get('content-type', 'n/a')}"
            f"\n  body: {body_preview}"
        )
    except Exception:  # noqa: BLE001
        return ""


def _override_captcha_bypass(payload: object) -> None:
    if not isinstance(payload, dict):
        return

    response_data = payload.get("response")
    if isinstance(response_data, dict) and response_data.get("captcha_bypass") is False:
        response_data["captcha_bypass"] = True

    client_data = payload.get("client")
    if isinstance(client_data, dict) and client_data.get("captcha_bypass") is False:
        client_data["captcha_bypass"] = True


def _create_testing_token_with_retry(clerk_client: Clerk) -> str:
    """Fetch a Clerk testing token with exponential backoff on transient failures."""
    for attempt in range(MAX_API_RETRIES + 1):
        try:
            testing_token_response = clerk_client.testing_tokens.create()
            assert testing_token_response
            return testing_token_response.token
        except (ClerkBaseError, httpx.TransportError) as exc:
            is_retryable = (
                isinstance(exc, httpx.TransportError)
                or exc.status_code in RETRYABLE_API_STATUS_CODES
            )
            if not is_retryable or attempt == MAX_API_RETRIES:
                raise

            exponential_delay_ms = _compute_backoff_delay_ms(
                attempt, API_BASE_DELAY_MS, API_JITTER_MAX_MS
            )
            retry_after_ms = 0.0
            if isinstance(exc, ClerkBaseError) and (
                retry_after := exc.headers.get("retry-after")
            ):
                try:
                    retry_after_ms = float(retry_after) * 1000
                except ValueError:
                    retry_after_ms = 0.0

            delay_ms = min(
                max(retry_after_ms, exponential_delay_ms), API_MAX_RETRY_DELAY_MS
            )
            logger.warning(
                "Retrying Clerk testing token request (%s), attempt %d/%d, waiting %dms",
                exc.status_code
                if isinstance(exc, ClerkBaseError)
                else type(exc).__name__,
                attempt + 1,
                MAX_API_RETRIES,
                round(delay_ms),
            )
            time.sleep(delay_ms / 1000)

    raise AssertionError("Unreachable")


def _wait_route_retry(page: Page, delay_ms: float) -> None:
    if not page.is_closed():
        page.wait_for_timeout(delay_ms)
    else:
        time.sleep(delay_ms / 1000)


def setup_clerk_testing_token(page: Page, frontend_api_url: str | None = None):
    """
    Bypasses bot protection by appending the testing token in the Frontend API requests.

    Args:
        page: The Playwright page object
        frontend_api_url: Optional Frontend API URL override

    Raises:
        ValueError: If frontend API URL is not provided
    """

    browser_context = page.context
    if browser_context in _setup_contexts:
        logger.debug(
            "Clerk testing route handler already registered for this context, skipping duplicate setup"
        )
        return

    resolved_fapi_url = _resolve_frontend_api_url(frontend_api_url)

    if not (testing_token := os.environ.get("CLERK_TESTING_TOKEN")):
        if clerk_private_key := os.environ.get("CLERK_PRIVATE_KEY"):
            clerk_client = Clerk(
                bearer_auth=clerk_private_key,
            )

            # lets get a fresh token and store it in the env
            testing_token = _create_testing_token_with_retry(clerk_client)
        else:
            raise ValueError(
                "CLERK_TESTING_TOKEN or CLERK_PRIVATE_KEY is required to generate a test token"
            )

    api_url = _build_api_url_pattern(resolved_fapi_url)

    logger.debug("Adding clerk testing token to URL url=%s", api_url.pattern)

    def handle_route(route: Route, request: Request):
        """
        Inject the testing token into each Clerk API call driven by the frontend flow.
        """
        url = request.url

        parsed_url = urlparse(url)
        params = parse_qs(parsed_url.query)

        if testing_token:
            params[TESTING_TOKEN_PARAM] = [testing_token]

        new_query = urlencode(params, doseq=True)
        new_url = parsed_url._replace(query=new_query).geturl()

        logger.debug("rewriting URL old=%s new=%s", url, new_url)

        for attempt in range(MAX_ROUTE_RETRIES + 1):
            try:
                response = route.fetch(url=new_url)
                status = response.status

                if status in RETRYABLE_ROUTE_STATUS_CODES:
                    if attempt < MAX_ROUTE_RETRIES:
                        delay_ms = _compute_backoff_delay_ms(
                            attempt, ROUTE_BASE_DELAY_MS, ROUTE_JITTER_MAX_MS
                        )
                        logger.debug(
                            "Clerk FAPI returned %s, retrying (attempt %d/%d, delay %dms): %s",
                            status,
                            attempt + 1,
                            MAX_ROUTE_RETRIES,
                            round(delay_ms),
                            url,
                        )
                        _wait_route_retry(page, delay_ms)
                        continue

                    diagnostics = _format_response_diagnostics(response)
                    logger.warning(
                        "Clerk FAPI request failed with status %s after %d attempts: %s%s",
                        status,
                        MAX_ROUTE_RETRIES + 1,
                        url,
                        diagnostics,
                    )
                    route.fulfill(response=response)
                    return

                payload = response.json()
                _override_captcha_bypass(payload)
                route.fulfill(response=response, json=payload)
                return
            except Exception as exc:  # noqa: BLE001
                if attempt < MAX_ROUTE_RETRIES:
                    delay_ms = _compute_backoff_delay_ms(
                        attempt, ROUTE_BASE_DELAY_MS, ROUTE_JITTER_MAX_MS
                    )
                    logger.debug(
                        "Clerk FAPI request error, retrying (attempt %d/%d, delay %dms): %s (%s)",
                        attempt + 1,
                        MAX_ROUTE_RETRIES,
                        round(delay_ms),
                        url,
                        exc,
                    )
                    _wait_route_retry(page, delay_ms)
                    continue

                logger.warning(
                    "Clerk FAPI request failed after %d attempts: %s (%s)",
                    MAX_ROUTE_RETRIES + 1,
                    url,
                    exc,
                )
                try:
                    route.continue_(url=new_url)
                except Exception as continue_exc:  # noqa: BLE001
                    logger.error(
                        "Failed to continue Clerk FAPI route: %s", continue_exc
                    )
                return

    _setup_contexts.add(browser_context)
    try:
        browser_context.route(api_url, handle_route)
    except Exception:
        _setup_contexts.discard(browser_context)
        raise


def teardown_clerk_testing_token(
    page: Page, frontend_api_url: str | None = None
) -> None:
    """
    Remove the testing token from the Clerk API requests. Should only be used for debugging playwright.
    """

    resolved_fapi_url = _resolve_frontend_api_url(frontend_api_url)
    page.context.unroute(_build_api_url_pattern(resolved_fapi_url))
    _setup_contexts.discard(page.context)
