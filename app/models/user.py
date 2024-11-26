"""
Mirrors this model: https://clerk.com/docs/reference/backend-api/tag/Users#operation/GetUser
"""


from activemodel import BaseModel
from activemodel.mixins import TimestampsMixin, TypeIDMixin
from pydantic import field_validator


class User(BaseModel, TimestampsMixin, TypeIDMixin("user"), table=True):
    # id: uuid.UUID = Field(
    #     sa_column=Column(TypeIDType("user"), primary_key=True),
    #     default_factory=lambda: TypeID("user"),
    # )

    clerk_id: str

    @field_validator("clerk_id")
    @classmethod
    def clerk_id_must_match_format(cls, v: str) -> str:
        if not v.startswith("user_"):
            raise ValueError("Clerk ID does not look valid")
        return v.title()
