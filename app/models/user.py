"""
https://clerk.com/docs/reference/backend-api/tag/Users#operation/GetUser
"""

from activemodel import BaseModel
from sqlmodel import Field


class User(BaseModel, table=True):
    id: int = Field(default=None, primary_key=True)
    clerk_id: str

    # TODO update ext ID in clerk when created
    # TODO refresh from clerk
