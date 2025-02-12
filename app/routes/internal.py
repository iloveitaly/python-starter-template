from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from activemodel.session_manager import aglobal_session

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
        # NOTE this line could not be more important, look at the underlying implementation!
        Depends(aglobal_session),
        # make sure the user is auth'd via clerk to this endpoint
        Depends(authenticate_clerk_request_middleware),
        # inject a doctor record into the request state
        Depends(inject_user_record),
        # allow admins to switch to another doctor
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
