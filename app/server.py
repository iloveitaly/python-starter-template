"""
`fastapi` cli will automatically start a uvicorn server using this file
"""

from fastapi import FastAPI

from app.routes.middleware import add_middleware
from app.routes.static import mount_public_directory

from .environments import is_production
from .routes.internal import app as internal_app

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

mount_public_directory(app)
add_middleware(app)

app.include_router(internal_app)


@app.get("/items/{item_id}")
def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "q": q}
