from fastapi import APIRouter, FastAPI
from fastapi.openapi.utils import get_openapi


def generate_openapi_schema(app: FastAPI | APIRouter) -> dict:
    """
    Generate OpenAPI schema for the given FastAPI application.

    Args:
        app: The FastAPI application
        title: Optional title for the API (defaults to app name + "API")

    Returns:
        The OpenAPI schema as a dictionary
    """
    from app.routes.utils.openapi import simplify_operation_ids

    # Apply simplification to operation IDs
    simplify_operation_ids(app)

    # Get the OpenAPI schema
    schema_title = f"{app.__class__.__name__} API"
    return get_openapi(
        title=schema_title,
        version=getattr(app, "version", "0.1.0"),  # Default to 0.1.0 if not set
        routes=app.routes,
    )
