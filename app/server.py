"""
`fastapi` cli will automatically start a uvicorn server using this file.

Route method names are important as they will be used for the openapi spec which will in turn be used to generate a
JavaScript client which will use these methods.
"""

from fastapi import FastAPI

from .environments import is_production
from .routes.internal import internal_api_app
from .routes.middleware import add_middleware
from .routes.static import mount_public_directory
from .templates import render_template

fast_api_args = {}

# disable API documentation in production
if is_production():
    fast_api_args = {
        "docs_url": None,
        "redoc_url": None,
        "openapi_url": None,
    }

# set `version:` as GIT sha? Set `title:`? https://github.com/fastapiutils/fastapi-utils/blob/e9e7e2c834d703503a3bf5d5605db6232dd853b9/fastapi_utils/api_settings.py#L43

# TODO unclear how to type this correctly
api_app = FastAPI(**fast_api_args)  # type: ignore

mount_public_directory(api_app)

# TODO simplify openapi structure for better client generation
api_app.include_router(internal_api_app)

add_middleware(api_app)


@api_app.get("/hello")
async def index():
    from datetime import datetime

    return render_template("routes/index.html", {"date": datetime.now()})


@api_app.get("/healthcheck")
async def healthcheck():
    return {"status": "ok"}


@api_app.get("/items/{item_id}")
async def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "q": q}
