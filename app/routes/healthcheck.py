# TODO this needs to be integrated into the application

from fastapi import APIRouter, HTTPException
from starlette import status
from whenever import Instant

from app.models.user import User

healthcheck_api_app = APIRouter(tags=["private"])


@healthcheck_api_app.get("/healthcheck")
async def healthcheck():
    "basic uptime check"
    return {"status": "ok"}


@healthcheck_api_app.get("/status")
async def active_user_status():
    "check if users have logged in within the last day"

    last_24_hours = Instant.now().to_system_tz().subtract(hours=24)
    active_users = User.where(User.last_active_at > last_24_hours).count()  # type: ignore

    if active_users == 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        )

    return {"status": "ok"}
