"""
The react-router application is setup as an SPA. This file configures the fast API server to serve these assets.

There are some nuances we need to consider:

* The generated SPA API client use a specific host for access. This changes depending
  on the environment. This means, in order to run integration tests on the application
  we need to build the assets in an environment distinct from production, with the right
  target host configured.


"""

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.environments import is_production, is_staging, python_environment
from app.setup import get_root_path


def mount_public_directory(app: FastAPI):
    # TODO should be extracted into another env var
    if is_production() or is_staging():
        public_path = get_root_path() / "public"
    else:
        public_path = get_root_path() / "web/build" / python_environment() / "client"

    app.mount(
        "/assets",
        StaticFiles(directory=public_path / "assets", html=False),
        name="public",
    )

    @app.get("/", include_in_schema=False)
    async def javascript_index():
        return FileResponse(public_path / "index.html")

    return app
