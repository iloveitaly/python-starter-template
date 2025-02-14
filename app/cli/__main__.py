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
def dump_openapi():
    import json

    from app.server import api_app

    typer.echo(json.dumps(api_app.openapi()))


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


if __name__ == "__main__":
    app()
