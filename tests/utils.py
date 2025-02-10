from functools import lru_cache

from app import log
from app.configuration.clerk import clerk
from app.environments import is_testing

from app.models.user import User, UserRole

from tests.constants import (
    CLERK_DEV_ADMIN_EMAIL,
    CLERK_DEV_USER_EMAIL,
    CLERK_DEV_USER_PASSWORD,
)


def delete_all_clerk_users():
    import funcy_pipe as fp

    log.info("deleting all dev clerk users")

    if not is_testing():
        raise RuntimeError("cannot delete dev users outside of testing")

    _deleted_users = (
        clerk.users.list()
        | fp.filter(
            lambda user: user.email_addresses[0].email_address
            not in [CLERK_DEV_USER_EMAIL, CLERK_DEV_ADMIN_EMAIL]
        )
        | fp.pluck_attr("id")
        | fp.lmap(lambda uid: clerk.users.delete(user_id=uid))
    )


@lru_cache
def get_clerk_dev_user():
    """
    Get or generate a common dev user to login via clerk
    """

    user_list = clerk.users.list(email_address=[CLERK_DEV_USER_EMAIL])

    assert user_list is not None

    if len(user_list) == 1:
        user = user_list[0]
    elif len(user_list) == 0:
        user = clerk.users.create(
            request={
                "email_address": [CLERK_DEV_USER_EMAIL],
                "password": CLERK_DEV_USER_PASSWORD,
            }
        )
    else:
        raise ValueError("more than one user found")

    assert user

    return CLERK_DEV_USER_EMAIL, CLERK_DEV_USER_PASSWORD, user


@lru_cache
def get_clerk_admin_user():
    """
    Get or generate a common admin user to login via clerk
    """

    user_list = clerk.users.list(email_address=[CLERK_DEV_ADMIN_EMAIL])
    assert user_list is not None

    if len(user_list) == 1:
        user = user_list[0]
    elif len(user_list) == 0:
        user = clerk.users.create(
            request={
                "email_address": [CLERK_DEV_ADMIN_EMAIL],
                "password": CLERK_DEV_USER_PASSWORD,
            }
        )
    else:
        raise ValueError("more than one user found")

    assert user

    # create the admin user locally
    User.find_or_create_by(
        clerk_id=user.id, email=CLERK_DEV_ADMIN_EMAIL, role=UserRole.admin
    )

    return CLERK_DEV_ADMIN_EMAIL, CLERK_DEV_USER_PASSWORD, user
