from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from typeid import TypeID

from activemodel.types import TypeIDType

from ..configuration.clerk import CLERK_PRIVATE_KEY
from .admin import admin_api_app
from .dependencies.clerk import AuthenticateClerkRequest
from .dependencies.login_as import login_as
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
        Depends(login_as),
    ],
)

internal_api_app.include_router(admin_api_app)


class AppData(BaseModel, extra="forbid"):
    message: str = "Hello From Internal Python"
    # TODO we should be able to specify TypeID here, but pydantic serializers don't like it
    user_id: str


@internal_api_app.get("/")
def application_data(request: Request) -> AppData:
    return AppData(user_id=str(request.state.user.id))
