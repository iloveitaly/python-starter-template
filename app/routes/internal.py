from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ..configuration.clerk import CLERK_PRIVATE_KEY
from .dependencies.clerk import AuthenticateRequest

app = APIRouter(
    prefix="/internal/v1",
    dependencies=[Depends(AuthenticateRequest(CLERK_PRIVATE_KEY))],
)


class AppData(BaseModel, extra="forbid"):
    message: str = "Hello From Internal Python"


@app.get("/")
def read_root() -> AppData:
    return AppData()
