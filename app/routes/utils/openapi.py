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
    Simplify operation IDs so that generated clients have simpler api function names
    """

    found_route = False

    for route in app.routes:
        if isinstance(route, APIRoute):
            route.operation_id = route.name
            found_route = True

    if not found_route:
        log.warning("no routes found when simplifying operation ids")
