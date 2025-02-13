import funcy_pipe as fp
import structlog

from app.configuration.clerk import clerk
from app.environments import is_testing

from tests.constants import (
    CLERK_ALL_USERS_TO_PRESERVE,
)

# named logger for all test-specific logic to use
log = structlog.get_logger(logger_name="test")


def delete_all_clerk_users():
    "clerk dev instances can hold a max of ~100 users, in order to avoid hitting that limit, we delete all users except for the dev users"

    log.info("deleting all dev clerk users")

    if not is_testing():
        raise RuntimeError("cannot delete dev users outside of testing")

    _deleted_users = (
        clerk.users.list()
        | fp.filter(
            lambda user: user.email_addresses[0].email_address
            not in CLERK_ALL_USERS_TO_PRESERVE
        )
        | fp.pluck_attr("id")
        | fp.lmap(lambda uid: clerk.users.delete(user_id=uid))
    )
