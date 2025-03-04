"""
Logic for an API server. This is distinct from the "app" API server, which hosts static assets
and is authenticated via a clerk token, and is meant to be consumed by an external user.


It is locked to a specific
TODO

- [ ] organizations? what is the clerk data model?
- [ ] use sk_ for API key prefix
"""

import sentry_sdk
from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from starlette.routing import Host
from starlette_context import context
from typeid import TypeID
from typeid.errors import TypeIDException

from app.models.user import API_KEY_PREFIX, User
from sqlmodel import Field, SQLModel

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

UNAUTHORIZED_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid key",
)


def authenticate_api_request_middleware(
    request: Request, token: str = Depends(oauth2_scheme)
):
    try:
        token_as_typeid = TypeID.from_string(token)
    except TypeIDException:
        raise UNAUTHORIZED_EXCEPTION

    if token_as_typeid.prefix != API_KEY_PREFIX:
        raise UNAUTHORIZED_EXCEPTION

    api_user = User.get(api_key=token_as_typeid.uuid)

    if not api_user:
        raise UNAUTHORIZED_EXCEPTION

    if api_user.deleted_at:
        raise HTTPException(
            status_code=status.HTTP_410_GONE, detail="Your Account has Been Disabled"
        )

    request.state.api_user = api_user

    context["api_user"] = api_user

    sentry_sdk.set_user({"id": api_user.id, "email": api_user.email})
    sentry_sdk.set_extra("api_user", True)


external_api_app = APIRouter(
    prefix="/external/v1", dependencies=[Depends(authenticate_api_request_middleware)]
)


@external_api_app.get("/ping")
def external_api_ping():
    "basic uptime + API authentication check"
    return {"status": "ok"}
