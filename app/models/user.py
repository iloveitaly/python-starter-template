"""
Mirrors this model: https://clerk.com/docs/reference/backend-api/tag/Users#operation/GetUser
"""

# TODO should we create an organization?
# https://clerk.com/docs/reference/backend-api/tag/Organizations#operation/GetOrganization

from datetime import datetime
from enum import Enum

from typeid import TypeID

import sqlalchemy as sa
from activemodel import BaseModel
from activemodel.mixins import SoftDeletionMixin, TimestampsMixin, TypeIDMixin
from activemodel.types import TypeIDType
from sqlmodel import Column, Field

# NOTE usr_ is used for non-clerk prefix to avoid confusion
CLERK_OBJECT_PREFIX = "user"

# let's do it Stripe style :)
API_KEY_PREFIX = "sk_live"


class UserRole(str, Enum):
    normal = "normal"
    admin = "admin"


# usr vs user is intentionally used to differentiate from the clerk model, which also uses a prefix ID
class User(
    BaseModel, TimestampsMixin, SoftDeletionMixin, TypeIDMixin("usr"), table=True
):
    clerk_id: str = Field(unique=True, index=True)
    "external ID of the user in Clerk"

    email: str = Field(nullable=True, default=None)
    "email address of the user in Clerk, makes it easy to debug and find users"

    role: UserRole = Field(default=UserRole.normal)
    "role of the user, primarily to support superuser switching"

    last_active_at: datetime | None = Field(
        default=None,
        sa_type=sa.DateTime(timezone=True),  # type: ignore
    )
    "last time the user had an active session"

    api_key: TypeIDType | None = Field(
        sa_column=Column(
            TypeIDType(API_KEY_PREFIX), nullable=True, unique=True, index=True
        ),
        default=None,
        exclude=True,
    )

    def generate_api_key(self):
        api_key = TypeID(API_KEY_PREFIX)

        self.api_key = api_key  # type: ignore
        self.save()

        return api_key

    # organization_id: str

    def before_save(self):
        if not self.clerk_id.startswith(CLERK_OBJECT_PREFIX + "_"):
            raise ValueError(
                f"clerk_id must start with {CLERK_OBJECT_PREFIX + '_'}, got {self.clerk_id}"
            )

    # TODO should also check to ensure the value does not change, I think sqlalchemy stores this state somewhere?
