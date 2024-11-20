"""
Cache LLM input and response. Helpful for debugging.
"""

import hashlib

from activemodel import BaseModel
from sqlmodel import Field


def hash_prompt(prompt: str) -> str:
    return hashlib.sha256(prompt.encode()).hexdigest()


class LLMResponse(BaseModel, table=True):
    id: int = Field(default=None, primary_key=True)
    model: str
    response: str
    prompt: str
    prompt_hash: str
    category: str
    question_id: int | None
