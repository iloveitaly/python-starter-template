"""
Without this transformation, you'll get very long function names in any generated code from the OpenAPI spec such as
`userListInternalV1AdminUsersGet`. This simplifies the operation ID to shrink generated function names.

Lifted from:

https://github.com/fastapiutils/fastapi-utils/blob/e9e7e2c834d703503a3bf5d5605db6232dd853b9/fastapi_utils/openapi.py#L7C5-L7C27
"""

import re
from collections import Counter

from fastapi import APIRouter, FastAPI
from fastapi.routing import APIRoute, RouteContext, iter_route_contexts
from fastapi.utils import generate_unique_id

from app import log
from app.utils.patching import hash_function_code


def _set_operation_id(context: RouteContext, operation_id: str) -> None:
    route = context.original_route
    assert isinstance(route, APIRoute)

    route.operation_id = operation_id

    # Included routers cache effective route state separately from the source route.
    if context._route_context is not None:
        context._route_context.operation_id = operation_id


# _complete_operation_id mirrors FastAPI's generate_unique_id implementation:
# https://github.com/fastapi/fastapi/blob/master/fastapi/utils.py#L95-L100
assert (
    hash_function_code(generate_unique_id)
    == "8474842e80b9b720daa51c36b5f718cd1a750169a80cdfd06457927f6df746f3"
)


def _complete_operation_id(*, name: str, path: str, method: str) -> str:
    operation_id = re.sub(r"\W", "_", f"{name}{path}")
    return f"{operation_id}_{method.lower()}"


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

    route_operation_ids = [
        (context, context.operation_id or context.name) for context in route_contexts
    ]
    operation_id_counts = Counter(
        operation_id for _context, operation_id in route_operation_ids
    )

    for context, operation_id in route_operation_ids:
        assert isinstance(operation_id, str)

        if operation_id_counts[operation_id] == 1:
            _set_operation_id(context, operation_id)
            continue

        assert context.methods
        assert context.path_format is not None
        method = next(iter(context.methods))
        complete_operation_id = _complete_operation_id(
            name=operation_id,
            path=context.path_format,
            method=method,
        )
        _set_operation_id(context, complete_operation_id)
