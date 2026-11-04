# TODO this needs to be integrated into the application

from fastapi import APIRouter, HTTPException
from starlette import status
from whenever import SYSTEM_TZ, Instant

from app.configuration.database import needs_alembic_migration
from app.routes.errors import ClientError

from app.models.user import User

healthcheck_api_app = APIRouter(tags=["private"])


@healthcheck_api_app.get("/healthcheck")
def healthcheck():
    """
    Uptime check and deploy gate.

    Fails when the database is unreachable (500, the connection raises) or behind this build's migrations (503), so
    a deploy whose migrations didn't run never goes healthy and the previous deploy stays live. A database *ahead* of
    this build (an older container during a rolling deploy) is healthy.

    A sync function so the database calls run in the threadpool rather than blocking the event loop.
    """

    if needs_alembic_migration():
        # a server-side condition rather than a client error, so HTTPException instead of ClientError
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="database migrations pending",
        )

    return {"status": "ok"}


@healthcheck_api_app.get("/status")
async def active_user_status():
    "check if users have logged in within the last day"

    last_24_hours = Instant.now().to_tz(SYSTEM_TZ).subtract(hours=24)
    active_users = User.where(User.last_active_at > last_24_hours).count()  # type: ignore

    if active_users == 0:
        raise ClientError(
            "No active users in the last 24 hours.",
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        )

    return {"status": "ok"}
