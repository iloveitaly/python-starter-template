"""
Lifted from: https://github.com/fastapiutils/fastapi-utils/blob/master/fastapi_utils/openapi.py#L7C5-L7C27
"""

from fastapi import FastAPI
from fastapi.routing import APIRoute


def simplify_operation_ids(app: FastAPI) -> None:
    """
    Simplify operation IDs so that generated clients have simpler api function names
    """
    for route in app.routes:
        if isinstance(route, APIRoute):
            route.operation_id = route.name
