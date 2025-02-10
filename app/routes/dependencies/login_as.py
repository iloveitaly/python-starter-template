from fastapi import Request

from app import log

from app.models.user import User, UserRole


def login_as(request: Request):
    """
    If we are an admin, check if we are logging in as a specific user
    """

    if (admin_user := request.state.user) and admin_user.role == UserRole.admin:
        # if we are an admin, let's check if we are logging in as another user
        login_as_clerk_id = request.session["login_as_user"]
        login_as_user = User.get(clerk_id=login_as_clerk_id)

        if not login_as_user:
            log.error("user not found", clerk_id=login_as_clerk_id)
            return

        # TODO should add admin ID for the user and update contextvars for logging
        request.state.user = login_as_user
