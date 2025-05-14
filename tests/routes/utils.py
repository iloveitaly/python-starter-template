import base64
import json
import typing as t

import itsdangerous
from cachetools import LRUCache, cached
from clerk_backend_api import CreateSessionRequestBody
from clerk_backend_api import User as ClerkUser
from clerk_backend_api.jwks_helpers import AuthStatus
from clerk_backend_api.jwks_helpers.authenticaterequest import RequestState
from decouple import config as decouple_config
from fastapi import Request, status
from httpx import Response

from app.configuration.clerk import clerk

from app.models.user import User, UserRole

from tests.constants import (
    CLERK_DEV_ADMIN_EMAIL,
    CLERK_DEV_SEED_EMAIL,
    CLERK_DEV_USER_EMAIL,
    CLERK_DEV_USER_PASSWORD,
)

# TODO this is a bit dangerous, let's see how it performs
clerk_cache_instance = LRUCache(maxsize=128)
"to cache user and session keys for all live clerk api interactions"


def base_server_url(protocol: t.Literal["http", "https"] = "https"):
    """
    VITE_PYTHON_URL is defined as the protocol + host, but the user/dev shouldn't have to worry
    about trailing slash, etc so we normalize it here.

    Note that the scheme is really important. The cookie middleware is setup to require
    https in order to set receive cookies, so if `http` is used instead of `https` this will
    break tests which require cookies.

    `https` requires that localias is setup, otherwise http (or some other SSL mechanism) must be used.
    """

    url = decouple_config("VITE_PYTHON_URL", cast=str).strip()

    # Remove any existing protocol
    if url.startswith(("http://", "https://")):
        url = url.split("://")[1]

    # Remove any trailing slashes
    url = url.rstrip("/")

    # Add protocol and trailing slash
    return f"{protocol}://{url}/"


@cached(cache=clerk_cache_instance)
def _get_or_create_clerk_user(email: str):
    user_list = clerk.users.list(request={"email_address": [email]})
    assert user_list is not None

    if len(user_list) == 1:
        return user_list[0]
    elif len(user_list) == 0:
        return clerk.users.create(
            request={
                "email_address": [email],
                "password": CLERK_DEV_USER_PASSWORD,
            }
        )
    else:
        raise ValueError("more than one user found")


def get_clerk_dev_user():
    """
    Get or generate a common dev user to login via clerk
    """
    user = _get_or_create_clerk_user(CLERK_DEV_USER_EMAIL)
    assert user

    return CLERK_DEV_USER_EMAIL, CLERK_DEV_USER_PASSWORD, user


def get_clerk_seed_user():
    """
    Get or generate a common dev user to login via clerk. Creates a local user record with a seed role.

    This user is used in both test and development environments.
    """
    user = _get_or_create_clerk_user(CLERK_DEV_SEED_EMAIL)
    assert user

    return CLERK_DEV_USER_EMAIL, CLERK_DEV_USER_PASSWORD, user


def get_clerk_admin_user():
    """
    Get or generate a common admin user to login via clerk. Creates a local user record with an admin role.
    """
    user = _get_or_create_clerk_user(CLERK_DEV_ADMIN_EMAIL)
    assert user

    # create the admin user locally
    _admin = User.find_or_create_by(
        clerk_id=user.id, email=CLERK_DEV_ADMIN_EMAIL, role=UserRole.admin
    )

    return CLERK_DEV_ADMIN_EMAIL, CLERK_DEV_USER_PASSWORD, user


class MockAuthenticateRequest:
    "mock out the clerk interactions, note that `authenticated_client` must be used here"

    async def __call__(self, request: Request) -> RequestState:
        _, _, user = get_clerk_dev_user()

        fake_auth_state = RequestState(
            status=AuthStatus.SIGNED_IN,
            reason=None,
            token="eyJhbGciOiJSUzI1NiIsImNhdCI6ImNsX0I3ZDRQRDExMUFBQSIsImtpZCI6Imluc18yb25uM1E3TkRmcndDNW9WWGd6R2U2dkExdTQiLCJ0eXAiOiJKV1QifQ.eyJleHAiOjE3MzY3ODk1ODgsImZ2YSI6Wy0xLC0xXSwiaWF0IjoxNzM2Nzg5NTI4LCJpc3MiOiJodHRwczovL3Jlc29sdmVkLWVtdS01My5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MzY3ODk1MTgsInNpZCI6InNlc3NfMnJhRnh2anVDUE5QRVFxaE8wdlFyMjVncjlvIiwic3ViIjoidXNlcl8ycmFGeHAzRENWUkZobnpqSlZpSDQ0Y2l2d3UifQ.DgnSSybWpG4ovKIDwDEvtnpMYOz8toWOJf8GXuftPIa0RiWp8EWpiX_m6fCTQBT3oCoR_BQXOEfTHtutzMYT5zmEL7FzDqBg_dE_dH9LJlq4s9WJ49pjWr1gfdMJF1okf0vdfROdKYnlCiKO4ocP1gM6s8hOPjRp_FTlFcj5bHhKSvRW63gmbeH-G-mZvxVkmXV7g9FeZ3idtSvzap8fBawYmhhqmtEa8-Re2Ikd1v3FxmnMcV2HPcKt1Kv9Vuo7oTC4_uMiX2MS-2EYt0Y5H6bkCyvbEmWmznIx2ZEnVQYFS36gpvjayEnr0uFK_jE1Uc7MIMgybueDqEcA1zqBjQ",
            payload={
                "exp": 1736789588,
                "fva": [-1, -1],
                "iat": 1736789528,
                # TODO should be dynamic
                "iss": "https://resolved-emu-53.clerk.accounts.dev",
                "nbf": 1736789518,
                "sid": "sess_2raFxvjuCPNPEQqhO0vQr25gr9o",
                "sub": user.id,
            },
        )
        # Attach the fake auth state to the request
        request.state.auth_state = fake_auth_state
        return fake_auth_state


@cached(cache=clerk_cache_instance, key=lambda user=None: user.id if user else None)
def get_valid_token(user: ClerkUser | None = None):
    "get a valid clerk session for a clerk user, the local user does not need to be created"

    if not user:
        _, _, user = get_clerk_dev_user()

    # now that we have a user, we need to create a session
    assert user.id
    session = clerk.sessions.create(request=CreateSessionRequestBody(user_id=user.id))
    assert session

    token = clerk.sessions.create_token(session_id=session.id)
    assert token

    return token.jwt


def decode_cookie(response: Response):
    "decode a signed cookie into a dict for inspection and assertion"
    from app.routes.middleware import SESSION_SECRET_KEY

    signer = itsdangerous.Signer(SESSION_SECRET_KEY)
    encrypted_cookie_value = response.cookies.get("session")

    if not encrypted_cookie_value:
        return {}

    decoded = signer.unsign(encrypted_cookie_value)
    session_data = json.loads(base64.b64decode(decoded))
    return session_data


def assert_status(response, status_code: int = status.HTTP_200_OK):  # noqa: F821
    assert response.status_code == status_code, response.json()
