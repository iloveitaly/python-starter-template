"""
Server entrypoint. Run by `uvicorn` to start the server.

`fastapi` cli will automatically start a uvicorn server using this file.

Notes:

- Route method names are important as they will be used for the openapi spec which will in turn be used to generate a
JavaScript client which will use these methods.
- APIRouters tagged "private" are excluded from OpenAPI spec dumps
"""

import typing as t

from fastapi import FastAPI

from app.constants import BUILD_COMMIT
from app.routes.api import external_api_app
from app.routes.errors import ErrorResponse, register_exception_handlers
from app.routes.utils.json_response import ORJSONSortedResponse
from app.routes.utils.openapi import simplify_operation_ids

from .environments import is_productionish
from .routes.authenticated import authenticated_api_app
from .routes.healthcheck import healthcheck_api_app
from .routes.middleware import add_middleware
from .routes.static import mount_public_directory
from .routes.unauthenticated import unauthenticated_api
from .routes.unauthenticated_html import unauthenticated_html

# used when generating openapi spec
fast_api_args = {"version": BUILD_COMMIT}

# disable API documentation in production
if is_productionish():
    fast_api_args = {
        "docs_url": None,
        "redoc_url": None,
        "openapi_url": None,
    }
else:
    fast_api_args = {
        "debug": True,
    }


COMMON_ERROR_RESPONSES: dict[int | str, dict[str, t.Any]] = {
    400: {"model": ErrorResponse},
    401: {"model": ErrorResponse},
    403: {"model": ErrorResponse},
    404: {"model": ErrorResponse},
    409: {"model": ErrorResponse},
    422: {"model": ErrorResponse},
    429: {"model": ErrorResponse},
}
"""
By default, fastapi uses HTTPValidationError for 422

We use a custom error structure and envelope for *all* application-level error responses.

This causes the definitions to end up in the openapi spec and properly typed on the python side.

https://github.com/fastapi/fastapi/blob/master/fastapi/openapi/utils.py#L457-L477
"""

# TODO not possible to type this properly :/ https://github.com/python/typing/discussions/1501
# NOTE `api_app` and not `app` is used intentionally here to make imports more specific
api_app = FastAPI(
    **fast_api_args,  # type: ignore
    default_response_class=ORJSONSortedResponse,
    responses=COMMON_ERROR_RESPONSES,
)

# requires clerk authentication
api_app.include_router(authenticated_api_app)

# requires api key authentication
api_app.include_router(external_api_app)

# public api, no authentication
api_app.include_router(unauthenticated_api)

api_app.include_router(unauthenticated_html)

# healthcheck endpoint, no authentication
api_app.include_router(healthcheck_api_app)

add_middleware(api_app)
register_exception_handlers(api_app)

# important that this is done after all routes are added
simplify_operation_ids(api_app)

# NOTE VERY IMPORTANT that this is done after all routes are added!!
mount_public_directory(api_app)
