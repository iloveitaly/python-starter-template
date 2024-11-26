"""
Cache LLM input and response. Helpful for debugging.
"""

import hashlib
import typing as t
import uuid

from activemodel import BaseModel
from activemodel.mixins import TimestampsMixin, TypeIDMixin
from activemodel.types.typeid import TypeIDType
from pydantic import field_validator, model_validator, validator
from sqlalchemy import Connection
from sqlalchemy.event import listens_for
from sqlalchemy.orm import Mapper
from sqlmodel import Column, Field
from typeid import TypeID


def hash_prompt(prompt: str) -> str:
    return hashlib.sha256(prompt.encode()).hexdigest()


class LLMResponse(BaseModel, TimestampsMixin, TypeIDMixin("llr"), table=True):
    model: str
    response: str
    prompt: str
    category: str

    # TODO is there a way to prevent a value from being provided via teh constructor
    prompt_hash: str | None = Field(default=None, nullable=False, exclude=True)

    def before_save(self):
        new_hash = hash_prompt(self.prompt)

        if self.prompt_hash and self.prompt_hash != new_hash:
            raise ValueError("Prompts should never be modified once they are cached")

        self.prompt_hash = new_hash

    # TODO https://github.com/fastapi/sqlmodel/discussions/805

    # @model_validator(mode="before")
    # @classmethod
    # def check_card_number_omitted(cls, data: t.Any) -> t.Any:
    #     breakpoint()
    #     if isinstance(data, dict):
    #         assert "card_number" not in data, "card_number should not be included"
    #     return data

    # @field_validator("prompt_hash")
    # @classmethod
    # def prevent_explicit_hash(cls, v):
    #     if v is not None:
    #         raise ValueError("prompt_hash cannot be set explicitly")
    #     return v


# @listens_for(LLMResponse, "before_update")
# def receive_before_commit(mapper: Mapper, connection: Connection, target: LLMResponse):
#     breakpoint()


# @listens_for(LLMResponse, "before_insert")
# def receive_before_insert(mapper: Mapper, connection: Connection, target: LLMResponse):
#     target.prompt_hash = hash_prompt(target.prompt)
#     # breakpoint()

# @field_validator("prompt", mode="before")
# def set_prompt_hash(cls, v, values):
#     values["prompt_hash"] = hash_prompt(v)
#     return v
