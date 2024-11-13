"""
`fastapi` cli will automatically start a uvicorn server using this file
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.setup import get_root_path

from .environments import is_production

fast_api_args = {}

# disable API documentation in production
if is_production():
    fast_api_args = {
        "docs_url": None,
        "redoc_url": None,
        "openapi_url": None,
    }

# TODO unclear how to type this correctly
app = FastAPI(**fast_api_args)  # type: ignore

app.mount(
    "/public",
    StaticFiles(directory=get_root_path() / "public", html=True),
    name="public",
)

# TODO set this up for the static frontend build
# app.mount("/static", StaticFiles(directory="static"), name="static")

# even in development, some sort of CORS is required
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AppData(BaseModel, extra="forbid"):
    message: str = "Hello From Python"


@app.get("/")
def read_root() -> AppData:
    return AppData()


@app.get("/items/{item_id}")
def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "q": q}
