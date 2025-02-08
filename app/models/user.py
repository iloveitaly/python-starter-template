"""
Mirrors this model: https://clerk.com/docs/reference/backend-api/tag/Users#operation/GetUser
"""

# TODO should we create an organization?
# https://clerk.com/docs/reference/backend-api/tag/Organizations#operation/GetOrganization

from datetime import datetime
from enum import Enum

from activemodel import BaseModel
from activemodel.mixins import SoftDeletionMixin, TimestampsMixin, TypeIDMixin
from sqlmodel import DateTime, Field

# NOTE we use usr_ for our prefix to avoid confusion
CLERK_OBJECT_PREFIX = "user_"


class UserRole(str, Enum):
    normal = "normal"
    admin = "admin"


# usr vs user is intentionally used to differentiate from the clerk model, which also uses a prefix ID
class User(
    BaseModel, TimestampsMixin, TypeIDMixin("usr"), SoftDeletionMixin, table=True
):
    clerk_id: str
    "external ID of the user in Clerk"

    email: str
    "email address of the user in Clerk, makes it easy to debug and find users"

    role: UserRole = Field(default=UserRole.normal)

    # organization_id: str

    def before_save(self):
        if not self.clerk_id.startswith(CLERK_OBJECT_PREFIX):
            raise ValueError(
                f"clerk_id must start with {CLERK_OBJECT_PREFIX}, got {self.clerk_id}"
            )

    # TODO should also check to ensure the value does not change, I think sqlalchemy stores this state somewhere?
