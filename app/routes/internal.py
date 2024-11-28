from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ..configuration.clerk import CLERK_PRIVATE_KEY
from .dependencies.clerk import AuthenticateRequest
from .dependencies.user import inject_user_record

internal_api_app = APIRouter(
    prefix="/internal/v1",
    # TODO unclear what the tags are used for...
    tags=["private"],
    dependencies=[
        Depends(AuthenticateRequest(CLERK_PRIVATE_KEY)),
        Depends(inject_user_record),
    ],
)


class AppData(BaseModel, extra="forbid"):
    message: str = "Hello From Internal Python"


@internal_api_app.get("/")
def application_data() -> AppData:
    return AppData()
