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
import re
from dataclasses import dataclass
from typing import Optional
from urllib.parse import parse_qs, urlencode, urlparse

from clerk_backend_api import Clerk
from playwright.sync_api import Page
from whenever import Instant

logger = logging.getLogger(__name__)


@dataclass
class SetupClerkTestingTokenOptions:
    frontend_api_url: Optional[str] = None


TESTING_TOKEN_PARAM = "__clerk_testing_token"

PUBLISHABLE_KEY_LIVE_PREFIX = "pk_live_"
PUBLISHABLE_KEY_TEST_PREFIX = "pk_test_"

# Matches publishable frontend API keys (e.g. foo-bar-13.clerk.accounts.dev)
PUBLISHABLE_FRONTEND_API_DEV_REGEX = (
    r"^(([a-z]+)-){2}([0-9]{1,2})\.clerk\.accounts([a-z.]*)(dev|com)$"
)


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

    has_valid_prefix = key.startswith(PUBLISHABLE_KEY_LIVE_PREFIX) or key.startswith(
        PUBLISHABLE_KEY_TEST_PREFIX
    )

    has_valid_postfix = base64_decode(
        key.split("_")[2] if len(key.split("_")) > 2 else ""
    ).endswith("$")

    return has_valid_prefix and has_valid_postfix


def parse_publishable_key(
    key: Optional[str],
    domain: Optional[str] = None,
    proxy_url: Optional[str] = None,
) -> Optional[PublishableKey]:
    if not key or not is_publishable_key(key):
        return None

    instance_type = (
        "development" if key.startswith(PUBLISHABLE_KEY_TEST_PREFIX) else "production"
    )

    frontend_api = base64_decode(key.split("_")[2])[:-1]

    if proxy_url:
        frontend_api = proxy_url
    elif instance_type != "development" and domain:
        frontend_api = f"clerk.{domain}"

    return PublishableKey(instance_type=instance_type, frontend_api=frontend_api)


def setup_clerk_testing_token(page: Page, frontend_api_url: str | None = None):
    """
    Bypasses bot protection by appending the testing token in the Frontend API requests.

    Args:
        page: The Playwright page object
        options: Optional configuration including frontend_api_url

    Raises:
        ValueError: If frontend API URL is not provided
    """

    if not frontend_api_url:
        frontend_api_url = os.environ.get("CLERK_FAPI_URL") or os.environ.get(
            "CLERK_FAPI"
        )

    if not frontend_api_url and (
        clerk_publishable_key := os.environ.get("CLERK_PUBLISHABLE_KEY")
    ):
        # the publishable key non-static component is base64 encoded version of the frontend api url
        if parsed_publishable_key := parse_publishable_key(clerk_publishable_key):
            frontend_api_url = parsed_publishable_key.frontend_api

    if not frontend_api_url:
        raise ValueError("Frontend API URL or valid publishable key is required")

    if not (testing_token := os.environ.get("CLERK_TESTING_TOKEN")):
        if clerk_private_key := os.environ.get("CLERK_PRIVATE_KEY"):
            clerk_client = Clerk(
                bearer_auth=clerk_private_key,
            )

            # lets get a fresh token and store it in the env
            testing_token_response = clerk_client.testing_tokens.create()
            assert testing_token_response
            testing_token = testing_token_response.token
        else:
            raise ValueError(
                "CLERK_TESTING_TOKEN or CLERK_PRIVATE_KEY is required to generate a test token"
            )

    api_url = re.compile(rf"^https://{re.escape(frontend_api_url)}/v1/.*?(\?.*)?$")

    logger.debug(f"Adding clerk testing token to URL url={api_url}")

    def handle_route(route, request):
        """
        Inject the testing token into each Clerk API call driven by the frontend flow.\
        """
        url = request.url

        parsed_url = urlparse(url)
        params = parse_qs(parsed_url.query)

        if testing_token:
            params[TESTING_TOKEN_PARAM] = [testing_token]

        new_query = urlencode(params, doseq=True)
        new_url = parsed_url._replace(query=new_query).geturl()

        logger.debug("rewriting URL old=%s new=%s", url, new_url)

        response = route.fetch(url=new_url)
        payload = response.json()

        if isinstance(payload, dict):
            response_data = payload.get("response")
            if (
                isinstance(response_data, dict)
                and response_data.get("captcha_bypass") is False
            ):
                response_data["captcha_bypass"] = True

            client_data = payload.get("client")
            if (
                isinstance(client_data, dict)
                and client_data.get("captcha_bypass") is False
            ):
                client_data["captcha_bypass"] = True

        route.fulfill(response=response, json=payload)

    page.route(api_url, handle_route)


def teardown_clerk_testing_token(
    page: Page, frontend_api_url: str | None = None
) -> None:
    """
    Remove the testing token from the Clerk API requests. Should only be used for debugging playwright.
    """

    if not frontend_api_url:
        parsed_result = parse_publishable_key(os.environ.get("CLERK_PUBLISHABLE_KEY"))
        assert parsed_result
        frontend_api_url = parsed_result.frontend_api

    page.unroute(f"https://{frontend_api_url}/v1/**")


def base64_decode(original_b64_string: str) -> str:
    """
    Decode a base64 encoded string, using the most appropriate method available.

    Py is touchy about having the right amount of whitespace in the input, so we add padding:
    https://stackoverflow.com/questions/2941995/python-ignore-incorrect-padding-error-when-base64-decoding
    """
    import base64

    b64_string = original_b64_string + "=" * ((4 - len(original_b64_string) % 4) % 4)

    return base64.b64decode(b64_string).decode("utf-8")
