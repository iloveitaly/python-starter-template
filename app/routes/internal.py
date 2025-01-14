from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ..configuration.clerk import CLERK_PRIVATE_KEY
from .dependencies.clerk import AuthenticateClerkRequest
from .dependencies.user import inject_user_record

# extract into variable for test import to easily override dependencies
authenticate_clerk_request_middleware = AuthenticateClerkRequest(CLERK_PRIVATE_KEY)

internal_api_app = APIRouter(
    prefix="/internal/v1",
    # TODO unclear what the tags are used for...
    tags=["private"],
    # think of dependencies as middleware
    dependencies=[
        Depends(authenticate_clerk_request_middleware),
        Depends(inject_user_record),
    ],
)


class AppData(BaseModel, extra="forbid"):
    message: str = "Hello From Internal Python"


@internal_api_app.get("/")
def application_data() -> AppData:
    return AppData()
