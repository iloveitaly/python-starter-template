"""
Cache LLM input and response. Helpful for debugging.
"""

import hashlib

from activemodel import BaseModel
from activemodel.mixins import TimestampsMixin, TypeIDMixin
from sqlmodel import Field


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
