"""
Admin-only routes:

- login_as / user impersonation
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Request
from pydantic import BaseModel as BasePydanticModel
from starlette import status

from app.models.user import User, UserRole

SESSION_KEY_LOGIN_AS_USER = "login_as_user"


def require_admin(request: Request):
    "Protect routes that require admin access"

    if (admin_user := request.state.user) and admin_user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)


admin_api_app = APIRouter(prefix="/admin", dependencies=[Depends(require_admin)])


class UserSwitchData(BasePydanticModel):
    clerk_id: str
    email: str


@admin_api_app.get("/users")
def user_list() -> list[UserSwitchData]:
    return list(
        User.select(User.clerk_id, User.email).where(User.role != UserRole.admin).all()
    )  # type: ignore


@admin_api_app.post("/login_as/{user_id}")
def login_as_user(request: Request, user_id: Annotated[str, Path()]):
    if request.state.user.clerk_id == user_id:
        request.session[SESSION_KEY_LOGIN_AS_USER] = None
        return

    login_as_user = User.where(
        User.role != UserRole.admin, User.clerk_id == user_id
    ).one()

    request.session[SESSION_KEY_LOGIN_AS_USER] = login_as_user.clerk_id  # type: ignore
    return
