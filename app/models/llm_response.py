"""
Cache LLM input and response. Helpful for debugging.
"""

import hashlib
import uuid

from activemodel import BaseModel
from sqlmodel import Column, Field
from typeid import TypeID

from app.typeid_sqlalchemy import TypeIDType


def hash_prompt(prompt: str) -> str:
    return hashlib.sha256(prompt.encode()).hexdigest()


class LLMResponse(BaseModel, table=True, arbitrary_types_allowed=True):
    # id: int = Field(default=None, primary_key=True)
    id: uuid.UUID = Field(
        # sa_column=mapped_column(
        #     TypeIDType("user"), primary_key=True, default=lambda: TypeID("user")
        # )
        sa_column=Column(TypeIDType("user"), primary_key=True),
        # primary_key=True,
        default_factory=lambda: TypeID("user"),
    )
    model: str
    response: str
    prompt: str
    prompt_hash: str | None = Field(default=None, nullable=False)
    category: str

    def before_save(self):
        self.prompt_hash = hash_prompt(self.prompt)
