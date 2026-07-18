import json
import typing as t

import itsdangerous
from httpx2 import Response

from app.env import env


def base_server_url(protocol: t.Literal["http", "https"] = "https"):
    """
    VITE_PYTHON_URL is defined as the protocol + host, but the user/dev shouldn't have to worry
    about trailing slash, etc so we normalize it here.

    Note that the scheme is really important. The cookie middleware is setup to require
    https in order to set receive cookies, so if `http` is used instead of `https` this will
    break tests which require cookies.

    `https` requires that localias is setup, otherwise http (or some other SSL mechanism) must be used.
    """

    url = env.str("VITE_PYTHON_URL")

    # Remove any existing protocol
    if url.startswith(("http://", "https://")):
        url = url.split("://")[1]

    # Remove any trailing slashes
    url = url.rstrip("/")

    # Add protocol and trailing slash
    return f"{protocol}://{url}/"


def bearer_headers(token: str) -> dict[str, str]:
    """Generate Authorization header with Bearer token."""
    return {"Authorization": f"Bearer {token}"}


def distribution_headers(distribution) -> dict[str, str]:
    """Generate Authorization header for distribution API key."""
    return bearer_headers(distribution.api_key)


def decode_cookie(response: Response):
    "decode a signed cookie into a dict for inspection and assertion"
    from app.routes.middleware import SESSION_SECRET_KEY

    from tests.utils import starlette_session_decode

    signer = itsdangerous.Signer(SESSION_SECRET_KEY)
    encrypted_cookie_value = response.cookies.get("session")

    if not encrypted_cookie_value:
        return {}

    decoded = signer.unsign(encrypted_cookie_value)
    session_data = json.loads(starlette_session_decode(decoded))
    return session_data
