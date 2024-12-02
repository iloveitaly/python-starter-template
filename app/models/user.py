"""
Mirrors this model: https://clerk.com/docs/reference/backend-api/tag/Users#operation/GetUser
"""

# TODO should we create an organization?
# https://clerk.com/docs/reference/backend-api/tag/Organizations#operation/GetOrganization

from datetime import datetime

from activemodel import BaseModel
from activemodel.mixins import TimestampsMixin, TypeIDMixin
from sqlmodel import DateTime, Field

# NOTE we use usr_ for our prefix to avoid confusion
CLERK_OBJECT_PREFIX = "user_"


# usr vs user is intentionally used to differentiate from the clerk model, which also uses a prefix ID
class User(BaseModel, TimestampsMixin, TypeIDMixin("usr"), table=True):
    clerk_id: str

    # TODO can we implement a deleted_at mixin with a decorator to handle deleted_at?
    # TODO can we implement a constraint check deleted && deleted_at
    deleted: bool = Field(default=False, nullable=False)
    deleted_at: datetime = Field(
        default=None,
        nullable=True,
        # TODO https://github.com/fastapi/sqlmodel/discussions/1228
        sa_type=DateTime(timezone=True),  # type: ignore
    )

    # organization_id: str

    def before_save(self):
        if not self.clerk_id.startswith(CLERK_OBJECT_PREFIX):
            raise ValueError(
                f"clerk_id must start with {CLERK_OBJECT_PREFIX}, got {self.clerk_id}"
            )

    # TODO should also check to ensure the value does not change, I think sqlalchemy stores this state somewhere?
