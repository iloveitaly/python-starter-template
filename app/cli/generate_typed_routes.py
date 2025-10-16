#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "fastapi",
#     "jinja2",
#     "click",
#     "structlog-config",
# ]
# ///

from pathlib import Path

import click
from jinja2 import Template
from structlog_config import configure_logger

log = configure_logger()

MODULE_TEMPLATE = '''\
"""Auto-generated typed url_path_for functions for FastAPI apps."""
# This file is auto-generated. Do not edit manually.

from typing import overload, Literal
{% for app_info in apps %}
from {{ app_info.import_path }} import {{ app_info.name }}
{% endfor %}

{% for app_info in apps %}
# Routes for {{ app_info.name }}
{% for route in app_info.routes %}
@overload
def {{ app_info.prefix }}_url_path_for(name: Literal["{{ route.name }}"], **path_params) -> str: ...
{% endfor %}

def {{ app_info.prefix }}_url_path_for(name: str, **path_params) -> str:
    """Type-safe wrapper around {{ app_info.name }}.url_path_for() with overloads for all routes."""
    return {{ app_info.name }}.url_path_for(name, **path_params)

{% endfor %}
'''


def extract_routes(app):
    """Extract route information from a FastAPI app."""
    routes = []

    for route in app.routes:
        if hasattr(route, "name") and route.name:
            routes.append(
                {
                    "name": route.name,
                    "path": route.path,
                }
            )

    # Sort for consistent output
    routes.sort(key=lambda x: x["name"])

    log.info("extracted_routes", count=len(routes))
    return routes


def load_app(app_module: str, prefix: str | None):
    """Load a FastAPI app and extract its information."""
    module_path, app_name = app_module.split(":")
    module = __import__(module_path, fromlist=[app_name])
    app = getattr(module, app_name)

    log.info("app_loaded", module=module_path, app=app_name)

    routes = extract_routes(app)

    # Determine prefix - default to app_name if not provided
    if prefix is None:
        prefix = app_name
        log.info("using_default_prefix", prefix=prefix)

    return {
        "import_path": module_path,
        "name": app_name,
        "prefix": prefix,
        "routes": routes,
    }


def generate_typed_module(apps_info: list[dict], output_path: Path):
    """Generate Python module with typed url_path_for functions."""

    log.info(
        "generating_module", output_path=str(output_path), app_count=len(apps_info)
    )

    # Render the template
    template = Template(MODULE_TEMPLATE)
    output = template.render(apps=apps_info)

    # Create parent directories if needed
    output_path.parent.mkdir(parents=True, exist_ok=True)

    output_path.write_text(output)

    total_routes = sum(len(app["routes"]) for app in apps_info)
    log.info(
        "module_generated", output_path=str(output_path), total_routes=total_routes
    )


@click.command()
@click.option(
    "--app-module",
    multiple=True,
    required=True,
    help="Python module path to FastAPI app (e.g., 'myapp.main:api_app'). Can be specified multiple times.",
)
@click.option(
    "--output",
    type=click.Path(path_type=Path),
    required=True,
    help="Output path for the generated module (required)",
)
@click.option(
    "--prefix",
    multiple=True,
    default=None,
    help="Prefix for the generated function (default: uses app variable name). Should match order of --app-module.",
)
def main(app_module: tuple[str, ...], output: Path, prefix: tuple[str, ...] | None):
    """Generate typed url_path_for functions for FastAPI applications."""

    log.info("starting_generation", app_modules=app_module, output=str(output))

    try:
        # Parse prefixes - if provided, must match number of apps
        prefixes = list(prefix) if prefix else [None] * len(app_module)

        if len(prefixes) != len(app_module):
            raise click.ClickException(
                f"Number of prefixes ({len(prefixes)}) must match number of app modules ({len(app_module)})"
            )

        # Load all apps
        apps_info = []
        for app_mod, app_prefix in zip(app_module, prefixes):
            app_info = load_app(app_mod, app_prefix)
            apps_info.append(app_info)

        # Generate module
        generate_typed_module(apps_info, output)

    except Exception as e:
        log.error("generation_failed", error=str(e), exc_info=True)
        raise click.ClickException(str(e))


if __name__ == "__main__":
    main()
