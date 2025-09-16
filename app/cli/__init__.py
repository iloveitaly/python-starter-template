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
def dump_openapi(
    app_target: str = "api_app",
    list_apps: bool = typer.Option(
        False,
        "--list-apps",
        help="List available FastAPI app targets and exit",
    ),
):
    """
    Dump OpenAPI schema for the specified app target.
    """
    import importlib
    import json

    from app.utils.openapi import generate_openapi_schema

    # Dynamically get the target app from app.server module
    server_module = importlib.import_module("app.server")

    def is_fastapi_app(name):
        if name.startswith("_"):
            return False

        obj = getattr(server_module, name)
        return hasattr(obj, "routes")

    available_apps = [name for name in dir(server_module) if is_fastapi_app(name)]

    if list_apps:
        typer.echo(
            "Available FastAPI app targets:\n"
            + "\n".join(f"- {n}" for n in available_apps)
        )
        return

    if app_target not in available_apps:
        typer.echo(
            f"Error: '{app_target}' not found.\n\nAvailable FastAPI app targets:\n"
            + "\n".join(f"- {n}" for n in available_apps)
        )
        raise typer.Exit(1)

    target_app = getattr(server_module, app_target)
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


@app.command()
def migrate():
    """
    Run migrations on the database. This is helpful when running a `release:` command before
    deployment to migrate your database. Alternatively, you can automatically run migrations during startup,
    but this is not good practice
    """
    from app.configuration.database import run_migrations

    run_migrations()
