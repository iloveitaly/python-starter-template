"""
Without this transformation, you'll get very long function names in any generated code from the OpenAPI spec such as
`userListInternalV1AdminUsersGet`. This simplifies the operation ID to shrink generated function names.

Lifted from:

https://github.com/fastapiutils/fastapi-utils/blob/e9e7e2c834d703503a3bf5d5605db6232dd853b9/fastapi_utils/openapi.py#L7C5-L7C27
"""

from collections import Counter

from fastapi import APIRouter, FastAPI
from fastapi.routing import APIRoute, iter_route_contexts

from app import log


def simplify_operation_ids(app: FastAPI | APIRouter) -> None:
    """
    Simplify operation IDs so that generated clients have simpler api function names.

    Restore FastAPI's complete operation ID for every route with a colliding name.
    """
    route_contexts = [
        context
        for context in iter_route_contexts(app.routes)
        if isinstance(context.original_route, APIRoute)
    ]
    if not route_contexts:
        log.warning("no routes found when simplifying operation ids")
        return

    for context in route_contexts:
        context.original_route.operation_id = None

    # Rebuild contexts so FastAPI regenerates complete IDs from the effective nested paths.
    route_contexts = [
        context
        for context in iter_route_contexts(app.routes)
        if isinstance(context.original_route, APIRoute)
    ]
    route_name_counts = Counter(context.name for context in route_contexts)

    for context in route_contexts:
        if route_name_counts[context.name] > 1:
            context.original_route.operation_id = context.unique_id
            continue

        context.original_route.operation_id = context.name
