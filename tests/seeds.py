from app.models.user import User

from tests.log import log
from tests.routes.utils import get_clerk_seed_user


def seed_test_data():
    ""
    log.info("creating test fixture data")

    username, password, user = get_clerk_seed_user()
    user = User.find_or_create_by(clerk_id=user.id)  # noqa: F821
