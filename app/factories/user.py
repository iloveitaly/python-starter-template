"""
Factories for the User model.
"""

from polyfactory import Use
from typeid import TypeID

from app.factories.clerk import get_clerk_dev_user

from activemodel.pytest.factories import ActiveModelFactory
from app.models.user import CLERK_OBJECT_PREFIX, User


class UserFactory(ActiveModelFactory[User]):
    clerk_id = Use(lambda: str(TypeID(CLERK_OBJECT_PREFIX)))


class UserWithClerkFactory(UserFactory):
    clerk_id = Use(lambda: get_clerk_dev_user()[2].id)

    @classmethod
    def default(cls) -> User:
        email, _, clerk_user = get_clerk_dev_user()

        user = User.find_or_create_by(clerk_id=clerk_user.id)
        if not user.email:
            user.email = email
        user.save()

        return user
