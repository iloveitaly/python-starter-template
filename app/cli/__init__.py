import json

import typer
from fastapi.routing import APIRoute

app = typer.Typer()


@app.command()
def write_versions():
    """
    Write chrome, redis, and postgres versions to disk.

    Helpful to automatically ensuring dev, test, and prod parity
    """

    from app.configuration.versions import (
        VERSIONS_FILE,
        chrome_version,
        postgres_version,
        redis_version,
    )

    VERSIONS_FILE.write_text(
        json.dumps(
            {
                "chrome": chrome_version(),
                "postgres": postgres_version(),
                "redis": redis_version(),
            },
            indent=2,
        )
    )


@app.command()
def dump_openapi(app_target: str = "api_app"):
    """
    Dump OpenAPI schema for the specified app target.
    """
    import importlib
    import json

    from app.utils.openapi import generate_openapi_schema

    # Dynamically get the target app from app.server module
    server_module = importlib.import_module("app.server")
    available_apps = [
        name
        for name in dir(server_module)
        # TODO is this a fastapi router? Probably a better way to do this?
        if not name.startswith("_") and hasattr(getattr(server_module, name), "routes")
    ]

    if app_target not in available_apps:
        typer.echo(
            f"Error: '{app_target}' not found. Available targets: {', '.join(available_apps)}"
        )
        raise typer.Exit(1)

    target_app = getattr(server_module, app_target)

    # Use our utility function
    openapi = generate_openapi_schema(target_app)

    typer.echo(json.dumps(openapi))


@app.command()
def routes():
    "output list of routes available in the application"

    from app.server import api_app

    for route in api_app.routes:
        if isinstance(route, APIRoute):
            methods = sorted(route.methods)
            method = ", ".join(methods)
            typer.echo(f"{method}   {route.path}    {route.name}")
        else:
            typer.echo(f"unsupported route: {route}")
