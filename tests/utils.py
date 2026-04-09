import base64
import typing as t

from tenacity import retry, stop_after_attempt


def base64_decode(original_b64_string: str | bytes, url_safe: bool = False) -> bytes:
    """
    Decode a base64 encoded string, adding padding if necessary.
    """

    if isinstance(original_b64_string, str):
        original_b64_string = original_b64_string.encode("ascii")

    # Py is touchy about having the right amount of whitespace in the input, so we add padding:
    # https://stackoverflow.com/questions/2941995/python-ignore-incorrect-padding-error-when-base64-decoding
    b64_string = original_b64_string + b"==" * ((4 - len(original_b64_string) % 4) % 4)

    if url_safe:
        return base64.urlsafe_b64decode(b64_string)

    return base64.b64decode(b64_string)


def starlette_session_decode(decoded_signed_value: bytes) -> bytes:
    """
    Specifically handles decoding the payload from a Starlette session cookie.

    Starlette 1.0.0 uses TimestampSigner which includes a dot-separated timestamp
    after the base64-encoded data.
    """

    data = decoded_signed_value
    if b"." in data:
        data = data.split(b".")[0]

    return base64_decode(data, url_safe=True)


from app.configuration.clerk import clerk
from app.environments import is_testing
from app.utils.geolocation import get_cached_public_ip

from tests.constants import (
    CLERK_ALL_USERS_TO_PRESERVE,
)

from .log import log


def get_public_ip_address() -> str | None:
    """
    Get the current public IP address of this server. Helpful when you have geolocation stuff that is
    dependent on a clients IP address.

    Returns:
        The public IP address as a string, or None if the request fails
    """
    return get_cached_public_ip()


@retry(stop=stop_after_attempt(3))
def delete_all_clerk_users():
    "clerk dev instances can hold a max of ~100 users, in order to avoid hitting that limit, we delete all users except for the dev users"

    log.info("deleting all dev clerk users")

    if not is_testing():
        raise RuntimeError("cannot delete dev users outside of testing")

    for user in clerk.users.list():
        if user.email_addresses[0].email_address not in CLERK_ALL_USERS_TO_PRESERVE:
            clerk.users.delete(user_id=user.id)
