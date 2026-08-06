"""
Completely unauthenticated API routes.

`/ping` and `/aping` intentionally exercise FastAPI's synchronous and asynchronous
route paths in automated unit tests.
"""

from fastapi import APIRouter, Depends

from activemodel.session_manager import aglobal_session

unauthenticated_api = APIRouter(
    prefix="/unauthenticated",
    dependencies=[
        # NOTE this line could not be more important, look at the underlying implementation!
        Depends(aglobal_session),
    ],
)


@unauthenticated_api.get("/ping")
def unauthenticated_ping():
    return {"status": "ok"}


@unauthenticated_api.get("/aping")
async def unauthenticated_aping():
    return {"status": "ok"}
