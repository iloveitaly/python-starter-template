"""
Structured, simple access log with request timing.

Adapte from:

- https://github.com/iloveitaly/fastapi-logger/blob/main/fastapi_structlog/middleware/access_log.py#L70
- https://github.com/fastapiutils/fastapi-utils/blob/master/fastapi_utils/timing.py
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


def get_client_addr(scope: Scope) -> str:
    """Get the client's address.

    Args:
        scope (Scope): Current context.

    Returns:
        str: Client's address in the IP:PORT format.
    """
    client = scope.get("client")
    if not client:
        return ""
    ip, port = client
    return f"{ip}:{port}"


def add_access_log_middleware(
    app: FastAPI,
) -> None:
    @app.middleware("http")
    async def access_log_middleware(
        request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        scope = request.scope
        route_name = get_route_name(app, request.scope)

        if scope["type"] != "http":
            return await call_next(request)

        start = perf_counter()
        response = await call_next(request)

        assert start
        elapsed = perf_counter() - start

        log.info(
            f"{response.status_code} {scope['method']} {scope['path']}",
            time=round(elapsed * 1000),
            status=response.status_code,
            method=scope["method"],
            path=scope["path"],
            query=scope["query_string"].decode(),
            client_ip=get_client_addr(scope),
            route=route_name,
        )

        return response
