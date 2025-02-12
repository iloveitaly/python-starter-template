from fastapi import Request

from app import log
from app.routes.admin import SESSION_KEY_LOGIN_AS_USER

from app.models.user import User, UserRole


def login_as(request: Request):
    """
    If we are an admin, check if we are logging in as a specific user, and switch to that user.
    """

    # TODO we shouldn't hard code this :/
    if request.url.path.startswith("/internal/v1/admin"):
        return

    if (admin_user := request.state.user) and admin_user.role == UserRole.admin:
        if SESSION_KEY_LOGIN_AS_USER not in request.session:
            return

        # if we are an admin, let's check if we are logging in as another user
        login_as_clerk_id = request.session[SESSION_KEY_LOGIN_AS_USER]
        login_as_user = User.get(clerk_id=login_as_clerk_id)

        if not login_as_user:
            log.error("user not found", clerk_id=login_as_clerk_id)
            return

        log.info(
            "logging in as user",
            clerk_id=login_as_user.clerk_id,
            admin_id=admin_user.id,
        )

        # TODO should add admin ID for the user and update contextvars for logging
        request.state.admin_user = admin_user
        request.state.user = login_as_user
