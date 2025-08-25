"""
`fastapi` cli will automatically start a uvicorn server using this file.

Route method names are important as they will be used for the openapi spec which will in turn be used to generate a
JavaScript client which will use these methods.
"""

from typing import Any

import orjson
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.routes.api import external_api_app
from app.routes.errors import register_exception_handlers
from app.routes.utils.openapi import simplify_operation_ids

from .environments import is_production
from .routes.healthcheck import healthcheck_api_app
from .routes.internal import internal_api_app
from .routes.middleware import add_middleware
from .routes.static import mount_public_directory
from .routes.unauthenticated import unauthenticated_api
from .templates import render_template

fast_api_args = {}

# disable API documentation in production
if is_production():
    fast_api_args = {
        "docs_url": None,
        "redoc_url": None,
        "openapi_url": None,
    }


class ORJSONSortedResponse(JSONResponse):
    """
    Lifted from the non-sorted fastapi-built version. ORJSONResponse is much faster than JSONResponse, but it does
    not respect the order of the keys:

    https://stackoverflow.com/questions/64408092/how-to-set-response-class-in-fastapi
    """

    def render(self, content: Any) -> bytes:
        return orjson.dumps(content, option=orjson.OPT_NON_STR_KEYS)


# TODO should we set a debug flag? https://fastapi.tiangolo.com/reference/fastapi/?h=debug#fastapi.FastAPI--example
# TODO set `version:` as GIT sha? Set `title:`? https://github.com/fastapiutils/fastapi-utils/blob/e9e7e2c834d703503a3bf5d5605db6232dd853b9/fastapi_utils/api_settings.py#L43

# TODO not possible to type this properly :/ https://github.com/python/typing/discussions/1501
# NOTE `api_app` and not `app` is used intentionally here to make imports more specific
api_app = FastAPI(
    **fast_api_args,  # type: ignore
    default_response_class=ORJSONSortedResponse,
)

api_app.include_router(internal_api_app)
api_app.include_router(external_api_app)
api_app.include_router(unauthenticated_api)
api_app.include_router(healthcheck_api_app)

add_middleware(api_app)
register_exception_handlers(api_app)


@api_app.get("/hello")
async def index():
    from datetime import datetime

    return render_template("routes/index.html", {"date": datetime.now()})


# important that this is done after all routes are added
simplify_operation_ids(api_app)

# NOTE VERY IMPORTANT that this is done after all routes are added!!
mount_public_directory(api_app)
