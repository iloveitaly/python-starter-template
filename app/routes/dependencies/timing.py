"""
Simple FastAPI middleware for timing request handling at the endpoint level.

Adapted from: https://github.com/fastapiutils/fastapi-utils/blob/master/fastapi_utils/timing.py
"""

from time import perf_counter

from fastapi import FastAPI
from starlette.middleware.base import RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Match, Mount
from starlette.types import Scope

from app import log


def get_route_name(app: FastAPI, scope: Scope, prefix: str = "") -> str:
    """Generate a descriptive route name for timing metrics"""
    if prefix:
        prefix += "."

    route = next(
        (r for r in app.router.routes if r.matches(scope)[0] == Match.FULL), None
    )

    if hasattr(route, "endpoint") and hasattr(route, "name"):
        return f"{prefix}{route.endpoint.__module__}.{route.name}"  # type: ignore
    elif isinstance(route, Mount):
        return f"{type(route.app).__name__}<{route.name!r}>"
    else:
        return scope["path"]


def add_timing_middleware(
    app: FastAPI,
    prefix: str = "",
    exclude: str | None = None,
) -> None:
    """
    Adds middleware that records request timing metrics.

    The provided `prefix` is used when generating route names.
    If `exclude` is provided, timings for routes containing that substring will not be logged.
    """

    @app.middleware("http")
    async def timing_middleware(
        request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        route_name = get_route_name(app, request.scope, prefix)
        should_log = not (exclude and exclude in route_name)
        start = None

        if should_log:
            start = perf_counter()

        response = await call_next(request)

        if should_log:
            assert start

            elapsed = perf_counter() - start
            log.debug(
                "request performance",
                execution_time=round(elapsed, 2),
                route_name=route_name,
            )

        return response
