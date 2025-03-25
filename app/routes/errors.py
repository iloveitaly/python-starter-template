"""
Custom exceptions for the web application.

Helpful for managing control flow.
"""

from fastapi import status
from pydantic import BaseModel


class EarlyResponseException(Exception):
    """
    Throw this exception to stop execution and return a result, but not necessarily an error,
    """

    def __init__(
        self,
        *,
        data: dict | BaseModel,
        status: int = status.HTTP_200_OK,
    ):
        if isinstance(data, BaseModel):
            self.data = data.model_dump()
        else:
            self.data = data

        self.status = status
