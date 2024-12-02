import json

import typer
from sqlalchemy.testing.config import ident

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
def hello():
    typer.echo("Hello, World!")


if __name__ == "__main__":
    app()
