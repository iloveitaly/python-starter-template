from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from app.models.user import User


def inject_user_record(request: Request):
    clerk_user_id = request.state.auth_state.payload["sub"]
    user = User.find_or_create_by(clerk_user_id=clerk_user_id)

    if user.deleted:
        raise HTTPException(
            status_code=status.HTTP_410_GONE, detail="Your Account has Been Disabled"
        )

    request.state.user = user
