from functools import lru_cache

from app import log
from app.configuration.clerk import clerk

from tests.constants import CLERK_DEV_USER_EMAIL, CLERK_DEV_USER_PASSWORD


def delete_all_clerk_users():
    import funcy_pipe as fp

    log.info("deleting all dev clerk users")

    # TODO add more protections against prod

    _deleted_users = (
        clerk.users.list()
        | fp.filter(
            lambda user: user.email_addresses[0].email_address != CLERK_DEV_USER_EMAIL
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
    else:
        user = clerk.users.create(
            request={
                "email_address": [CLERK_DEV_USER_EMAIL],
                "password": CLERK_DEV_USER_PASSWORD,
            }
        )

    assert user

    return CLERK_DEV_USER_EMAIL, CLERK_DEV_USER_PASSWORD, user
