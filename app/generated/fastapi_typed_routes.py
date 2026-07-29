"""Auto-generated typed url_path_for functions for FastAPI apps."""

from typing import Literal, overload

from fastapi.routing import APIRoute, iter_route_contexts
from starlette.routing import NoMatchFound

from app.server import api_app

# Routes for api_app


@overload
def api_app_url_path_for(name: Literal["active_user_status"], **path_params) -> str: ...


@overload
def api_app_url_path_for(name: Literal["application_data"], **path_params) -> str: ...


@overload
def api_app_url_path_for(
    name: Literal["external_api_ping_external_v1_ping_get"], **path_params
) -> str: ...


@overload
def api_app_url_path_for(
    name: Literal["external_api_ping_internal_v1_ping_get"], **path_params
) -> str: ...


@overload
def api_app_url_path_for(name: Literal["frontend_handler"], **path_params) -> str: ...


@overload
def api_app_url_path_for(name: Literal["healthcheck"], **path_params) -> str: ...


@overload
def api_app_url_path_for(name: Literal["index"], **path_params) -> str: ...


@overload
def api_app_url_path_for(name: Literal["javascript_index"], **path_params) -> str: ...


@overload
def api_app_url_path_for(name: Literal["login_as_user"], **path_params) -> str: ...


@overload
def api_app_url_path_for(
    name: Literal["unauthenticated_ping"], **path_params
) -> str: ...


@overload
def api_app_url_path_for(name: Literal["user_list"], **path_params) -> str: ...


_api_app_qualified_route_ids = frozenset(
    (
        "external_api_ping_external_v1_ping_get",
        "external_api_ping_internal_v1_ping_get",
    )
)


def api_app_url_path_for(name: str, **path_params) -> str:
    """Type-safe wrapper around api_app.url_path_for() with overloads for all routes."""
    if name in _api_app_qualified_route_ids:
        for route_context in iter_route_contexts(api_app.routes):
            route = route_context.original_route
            if isinstance(route, APIRoute) and route_context.unique_id == name:
                return route_context.url_path_for(route.name, **path_params)
        raise NoMatchFound(name, path_params)

    return api_app.url_path_for(name, **path_params)
