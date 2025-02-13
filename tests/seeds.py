from app.models.user import User

from tests.routes.utils import get_clerk_seed_user
from tests.utils import log


def seed_test_data():
    ""
    log.info("creating test fixture data")

    username, password, user = get_clerk_seed_user()
    user = User.find_or_create_by(clerk_id=user.id)  # noqa: F821
