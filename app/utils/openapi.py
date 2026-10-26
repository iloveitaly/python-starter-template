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

    # apply simplification to operation IDs
    simplify_operation_ids(app)

    # get the OpenAPI schema
    schema_title = f"{app.__class__.__name__} API"
    return get_openapi(
        title=schema_title,
        # default to 0.1.0 if not set
        version=getattr(app, "version", "0.1.0"),
        routes=app.routes,
        # TODO If we are hosting the OpenAPI spec on a separate domain than the API is hosted on, then we must specify servers to point it to a, uh, different endpoint to hit.
        #      However, if the domain is the same, then we don't need to add this and retool will hit the same domain
        # servers=[{"url": "https://your.domain.com"}],
    )
