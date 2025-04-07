"""
Admin-only routes:

- login_as / user impersonation, similar to https://clerk.com/docs/users/user-impersonation but without a $100/month sub
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Request
from pydantic import BaseModel as BasePydanticModel
from pydantic import ConfigDict
from starlette import status
from typeid import TypeID

from app import log

from app.models.user import User, UserRole

SESSION_KEY_LOGIN_AS_USER = "login_as_user"


def require_admin(request: Request):
    "Protect routes that require admin access"

    if (admin_user := request.state.user) and admin_user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)


admin_api_app = APIRouter(prefix="/admin", dependencies=[Depends(require_admin)])


class UserSwitchData(BasePydanticModel):
    model_config = ConfigDict(from_attributes=True)

    clerk_id: str
    id: TypeID
    email: str | None


class UserListResponse(BasePydanticModel):
    current_user: UserSwitchData | None
    users: list[UserSwitchData]


@admin_api_app.get("/users")
def user_list(request: Request) -> UserListResponse:
    # remember, these routes are protected from the login_as functionality
    login_as_user = None

    if SESSION_KEY_LOGIN_AS_USER in request.session:
        login_as_clerk_id = request.session[SESSION_KEY_LOGIN_AS_USER]
        login_as_user = User.get(clerk_id=login_as_clerk_id)

    return UserListResponse(
        current_user=login_as_user,  # type: ignore
        users=list(
            User.select(User.clerk_id, User.email, User.id)
            .where(User.role != UserRole.admin)
            .all()
        ),  # type: ignore
    )


@admin_api_app.post("/login_as/{user_id}")
def login_as_user(request: Request, user_id: Annotated[str, Path()]):
    if request.state.user.clerk_id == user_id:
        log.info("removing login_as")
        request.session[SESSION_KEY_LOGIN_AS_USER] = None
        return

    login_as_user = User.where(
        User.role != UserRole.admin, User.clerk_id == user_id
    ).one()

    log.info("login_as_user", login_as_user=login_as_user)

    request.session[SESSION_KEY_LOGIN_AS_USER] = login_as_user.clerk_id  # type: ignore
    return
