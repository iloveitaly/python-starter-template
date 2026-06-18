import json

import typer

# disable rich tracebacks in favor of beautiful_traceback
app = typer.Typer(pretty_exceptions_enable=False)


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
        python_version,
        redis_version,
    )

    VERSIONS_FILE.write_text(
        json.dumps(
            {
                "chrome": chrome_version(),
                "postgres": postgres_version(),
                "redis": redis_version(),
                # this is already defined via mise, but to alert the developer of venv issues we duplicate it here
                "python": python_version(),
            },
            indent=2,
        )
    )


@app.command()
def dump_openapi(
    tag: str | None = typer.Argument(
        None,
        help="Filter routes by tag (in addition to always excluding 'private')",
    ),
    list_tags: bool = typer.Option(
        False,
        "--list-tags",
        help="List available (non-private) tags and exit",
    ),
):
    """
    Dump OpenAPI schema, excluding routes tagged 'private'.

    We tried generating by route object, but this caused COMMON_ERROR_RESPONSES (the app-level 400/401/etc
    response definitions) to be hidden from the api spec. This is why we use the tagged approach.
    """
    import importlib

    from fastapi.openapi.utils import get_openapi
    from fastapi.routing import APIRoute

    server_module = importlib.import_module("app.server")
    parent_app = server_module.api_app

    public_routes = [
        r
        for r in parent_app.router.routes
        if isinstance(r, APIRoute) and "private" not in (r.tags or [])
    ]

    if list_tags:
        available_tags = sorted({str(t) for r in public_routes for t in (r.tags or [])})
        if available_tags:
            typer.echo(
                "Available tags:\n" + "\n".join(f"- {t}" for t in available_tags)
            )
        else:
            typer.echo("No tags available — all public routes are untagged.")
        return

    filtered_routes = (
        [r for r in public_routes if tag in (r.tags or [])]
        if tag is not None
        else public_routes
    )

    if tag is not None and not filtered_routes:
        available_tags = sorted({str(t) for r in public_routes for t in (r.tags or [])})
        typer.echo(
            f"Error: no routes found with tag '{tag}'.\n\nAvailable tags:\n"
            + "\n".join(f"- {t}" for t in available_tags)
        )
        raise typer.Exit(1)

    schema = get_openapi(
        title=parent_app.title,
        version=parent_app.version,
        openapi_version=parent_app.openapi_version,
        description=parent_app.description or "",
        routes=filtered_routes,
    )

    typer.echo(json.dumps(schema))


@app.command()
def routes():
    "output list of routes available in the application"

    from fastapi.routing import APIRoute

    from app.server import api_app

    for route in api_app.routes:
        if isinstance(route, APIRoute):
            methods = sorted(route.methods or ())
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
