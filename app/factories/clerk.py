from cachetools import LRUCache, cached

from app.factories.constants import (
    CLERK_DEV_ADMIN_EMAIL,
    CLERK_DEV_SEED_EMAIL,
    CLERK_DEV_USER_EMAIL,
    CLERK_DEV_USER_PASSWORD,
)
from app.helpers.clerk import get_or_create_clerk_user

from app.models.user import User, UserRole

# TODO this is a bit dangerous, let's see how it performs
clerk_cache_instance = LRUCache(maxsize=128)
"to cache user and session keys for all live clerk api interactions"


@cached(cache=clerk_cache_instance)
def _get_or_create_clerk_user(email: str):
    return get_or_create_clerk_user(email, password=CLERK_DEV_USER_PASSWORD)


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
