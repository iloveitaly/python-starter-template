import shutil
import subprocess

import funcy_pipe as fp

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


def delete_all_clerk_users():
    "clerk dev instances can hold a max of ~100 users, in order to avoid hitting that limit, we delete all users except for the dev users"

    log.info("deleting all dev clerk users")

    if not is_testing():
        raise RuntimeError("cannot delete dev users outside of testing")

    _deleted_users = (
        clerk.users.list()
        | fp.filter(
            lambda user: (
                user.email_addresses[0].email_address not in CLERK_ALL_USERS_TO_PRESERVE
            )
        )
        | fp.pluck_attr("id")
        | fp.lmap(lambda uid: clerk.users.delete(user_id=uid))
    )


def run_just_recipe(recipe: str, **kwargs) -> str:
    """
    Run a just recipe and ensure it succeeds.

    Args:
        recipe: The name of the just recipe to run.
        **kwargs: Additional keyword arguments to pass to `subprocess.run`.

    Returns:
        The standard output of the command as a string.
    """
    # Check if 'just' is in path
    if not shutil.which("just"):
        # Fallback for environments without just in PATH (like some CIs or local dev)
        # Assuming just is installed via some means, or skipping if not found
        # But for this test, it's critical.
        raise FileNotFoundError(
            "just executable not found in PATH. Ensure just is installed and in PATH/setup is correct."
        )

    try:
        result = subprocess.run(
            ["just", recipe],
            check=True,
            capture_output=True,
            text=True,
            **kwargs,
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        # Capture stderr for debugging
        raise RuntimeError(f"just {recipe} failed:\n{e.stderr}") from e
