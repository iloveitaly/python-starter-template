"""
Factories to quickly generate both test and dev data.

Polyfactory is powerful, but dangerous. Make sure you understand the nuances of how it works with pydantic
models.
"""

from polyfactory import Ignore
from typeid import TypeID

from activemodel.pytest.factories import ActiveModelFactory
from app.models.user import CLERK_OBJECT_PREFIX, User


class UserFactory(ActiveModelFactory[User]):
    # TODO cleanup these prefixes
    clerk_id = lambda: str(TypeID(CLERK_OBJECT_PREFIX[0:-1]))
    api_key = Ignore()

    @classmethod
    def post_build(cls, model):
        model.generate_api_key()
