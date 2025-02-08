from fastapi import HTTPException, Request, status

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

    request.state.user = user
