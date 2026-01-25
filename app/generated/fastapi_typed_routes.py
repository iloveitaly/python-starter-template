"""Auto-generated typed url_path_for functions for FastAPI apps."""
# This file is auto-generated. Do not edit manually.

from typing import Literal, overload

from app.server import api_app

# Routes for api_app

@overload
def api_app_url_path_for(name: Literal["active_user_status"], **path_params) -> str: ...

@overload
def api_app_url_path_for(name: Literal["application_data"], **path_params) -> str: ...

@overload
def api_app_url_path_for(name: Literal["create_payment"], **path_params) -> str: ...

@overload
def api_app_url_path_for(name: Literal["external_api_ping"], **path_params) -> str: ...

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
def api_app_url_path_for(name: Literal["user_list"], **path_params) -> str: ...


def api_app_url_path_for(name: str, **path_params) -> str:
    """Type-safe wrapper around api_app.url_path_for() with overloads for all routes."""
    return api_app.url_path_for(name, **path_params)

