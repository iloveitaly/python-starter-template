"""
The react-router application is setup as a SPA. This logic configures the fast API server to serve the static SPA assets.

There are some nuances we need to consider:

* The generated SPA API client use a specific host for access. This changes depending
  on the environment. This means, in order to run integration tests on the application
  we need to build the assets in an environment distinct from production, with the right
  target host configured.

* In development, we don't want to statically serve the assets. We want to use live reloaded react for a fast dev loop.
  The logic here is only used in production and integration tests, which reduces the test coverage and makes this logic
  more risky.

* At-scale, it makes sense to host assets on a CDN. However, serving assets out of a single container simplifies the
  deployment process and should be performant enough for most applications.


"""

import mimetypes
import os

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.datastructures import Headers
from starlette.types import Scope

from app import log, root
from app.environments import (
    is_development,
    is_local_testing,
    is_production,
    is_staging,
    python_environment,
)
from app.utils.patching import hash_function_code

# make sure the underlying implementation here does not change significantly, since we are using undocumented APIs
assert (
    hash_function_code(StaticFiles.lookup_path)
    == "84c5a0e016a4c554aebf61d092be224b5c602538e44d1688bd3951198b06fddb"
)


class GZipStaticFiles(StaticFiles):
    "Check for a precompressed gz file and serve that instead. Loosely based on GZipMiddleware"

    async def get_response(self, path: str, scope: Scope):
        # GZipMiddleware checks the scope for HTTP
        if scope["type"] == "http":
            headers = Headers(scope=scope)
            if "gzip" in headers.get("Accept-Encoding", ""):
                # returns tuple where first element is a string full path on the local filesystem
                # and second is stat information
                full_path = self.lookup_path(path)[0]
                gz_path = full_path + ".gz"

                if os.path.exists(gz_path):
                    content_type, _ = mimetypes.guess_type(full_path)
                    headers = {"Content-Encoding": "gzip"}

                    return FileResponse(
                        gz_path,
                        # FileResponse uses `guess_type` but falls back to `text/plain`
                        media_type=(content_type or "text/plain"),
                        headers=headers,
                    )

        return await super().get_response(path, scope)


def mount_public_directory(app: FastAPI):
    # TODO should be extracted into another env var so it can be shared with JS
    if is_production() or is_staging():
        public_path = root / "public"
    else:
        public_path = root / "web/build" / python_environment() / "client"

    # in development, a separate py & js server will be used, if the development build DNE that's fine
    if not public_path.exists() and (is_development() or is_local_testing()):
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
        GZipStaticFiles(directory=public_path / "assets", html=False),
        name="public",
    )

    @app.get("/", include_in_schema=False)
    async def javascript_index():
        return FileResponse(public_path / "index.html")

    @app.get("/{path:path}")
    async def frontend_handler(path: str):
        """
        This is a very dangerous piece of code: if this is not last it will override other routes in the application

        Without this, non-index RR routes will not work. When a path is requested that does not exist in the fastapi
        application, it servers up the index.html file. Most likely, this path is a RR route.

        https://gist.github.com/ultrafunkamsterdam/b1655b3f04893447c3802453e05ecb5e
        """
        fp = public_path / path

        if not fp.exists():
            fp = public_path / "index.html"

        return FileResponse(fp)

    return app
