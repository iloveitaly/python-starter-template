import json

import typer

from app.configuration.versions import (
    VERSIONS_FILE,
    chrome_version,
    postgres_version,
    redis_version,
)

app = typer.Typer()


@app.command()
def write_versions():
    """
    Write chrome, redis, and postgres versions to disk.

    Helpful to automatically ensuring dev, test, and prod parity
    """

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


if __name__ == "__main__":
    app()
