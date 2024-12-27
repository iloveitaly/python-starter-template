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

from app import log, root
from app.environments import (
    is_development,
    is_production,
    is_staging,
    python_environment,
)


def mount_public_directory(app: FastAPI):
    # TODO should be extracted into another env var so it can be shared with JS
    if is_production() or is_staging():
        public_path = root / "public"
    else:
        public_path = root / "web/build" / python_environment() / "client"

    # in development, a separate py & js server will be used, if the development build DNE that's fine
    if not public_path.exists() and is_development():
        log.warning(
            "The development build does not exist. Static files will not be served"
        )
        return app

    if not public_path.exists():
        raise Exception(
            f"Client assets do not exist {public_path}. Please run `just py_js-build`"
        )

    app.mount(
        "/assets",
        StaticFiles(directory=public_path / "assets", html=False),
        name="public",
    )

    @app.get("/", include_in_schema=False)
    async def javascript_index():
        return FileResponse(public_path / "index.html")

    @app.get("/{path:path}")
    async def frontend_handler(path: str):
        """
        This is a very dangerous piece of code: if this is not last it will override other routes in the application

        Without this, non-index RR routes will not work.

        https://gist.github.com/ultrafunkamsterdam/b1655b3f04893447c3802453e05ecb5e
        """
        fp = public_path / path

        if not fp.exists():
            fp = public_path / "index.html"

        return FileResponse(fp)

    return app
