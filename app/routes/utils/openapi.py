"""
Without this transformation, you'll get very long function names in any generated code from the OpenAPI spec such as
`userListInternalV1AdminUsersGet`. This simplifies the operation ID to shrink generated function names.

Lifted from:

https://github.com/fastapiutils/fastapi-utils/blob/e9e7e2c834d703503a3bf5d5605db6232dd853b9/fastapi_utils/openapi.py#L7C5-L7C27
"""

from fastapi import APIRouter, FastAPI
from fastapi.routing import APIRoute

from app import log


def simplify_operation_ids(app: FastAPI | APIRouter) -> None:
    """
    Simplify operation IDs so that generated clients have simpler api function names.

    Walks the full route tree recursively. Included routers are wrapped in
    `_IncludedRouter` (with an `original_router` attribute), so we unwrap those too.
    """

    def _walk(router: FastAPI | APIRouter) -> bool:
        found = False
        for route in router.routes:
            if isinstance(route, APIRoute):
                # NOTE this is the core intention of this method: shorten the operation ID to the route name
                route.operation_id = route.name
                found = True
            else:
                # routes includes Mount/docs/etc.; only _IncludedRouter has original_router
                inner_router = getattr(route, "original_router", None)
                if inner_router is None:
                    # routes are not present when WebSocketRoute, docs route, etc is present (i.e. special cases)
                    inner_router = route if hasattr(route, "routes") else None

                if inner_router is not None and inner_router is not router:
                    found = _walk(inner_router) or found
        return found

    if not _walk(app):
        log.warning("no routes found when simplifying operation ids")
