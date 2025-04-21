"""
Completely unauthenticated API routes.
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
def create_payment():
    return {"status": "ok"}
