import shutil
import subprocess

import funcy_pipe as fp
from tenacity import retry, stop_after_attempt

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


def run_just_recipe(recipe: str, **kwargs) -> str:
    if not shutil.which("just"):
        raise FileNotFoundError(
            "just executable not found in PATH. Ensure just is installed and in PATH/setup is correct."
        )

    result = subprocess.run(
        ["just", recipe],
        check=True,
        capture_output=True,
        text=True,
        **kwargs,
    )

    return result.stdout
