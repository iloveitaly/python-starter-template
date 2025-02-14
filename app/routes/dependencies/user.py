from datetime import datetime

import sentry_sdk
from fastapi import HTTPException, Request, status
from starlette_context import context

from app.models.user import User


def inject_user_record(request: Request):
    """
    If a valid Clerk user is detected which is not in the DB, create it. Upstream logic talks to Clerk and makes sure
    the user is valid.
    """

    clerk_id = request.state.auth_state.payload["sub"]
    user = User.find_or_create_by(clerk_id=clerk_id)

    if user.deleted_at:
        raise HTTPException(
            status_code=status.HTTP_410_GONE, detail="Your Account has Been Disabled"
        )

    user.last_active_at = datetime.now()
    user.save()

    request.state.user = user

    context["user"] = user
    sentry_sdk.set_user({"id": user.id, "email": user.email})
