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
# https://github.com/encode/starlette/commit/bc3b4002e241353d96e1ad18d8c6b5fc4f8463df
assert (
    hash_function_code(StaticFiles.lookup_path)
    == "a3ebf7850a8389fc2d8328d7322745f233879bc300ab5cc1bd2a52a5e1710815"
)

# without this, the index file will be cached and therefore can easily serve stale content
# this did not cause an issue on Chrome, but Safari heavily caches files without these directives.
# https://claude.ai/share/882b6f3f-9212-41ae-9594-1c32f03b8825
HTML_NOCACHE_HEADERS = {
    # allow storage but require revalidation to avoid stale SPA shell
    "Cache-Control": "no-cache, max-age=0, must-revalidate",
    "Pragma": "no-cache",
    "Expires": "0",
    "Accept-Ranges": "none",
}

GZIP_HEADERS = {
    "Content-Encoding": "gzip",
    "Vary": "Accept-Encoding",
    # we don't support streaming, but if we don't explicitly say we can't do streaming (range request)
    # nginx will advertise and some bots/fancy browsers will attempt to do range requests causing
    # a flood of exceptions in our application. This never occurs right away, but as the files age
    # (if there's no recent deploys) clients will attempt to do range requests and you'll see a bunch of errors
    "Accept-Ranges": "none",
}


class GZipStaticFiles(StaticFiles):
    "Check for a precompressed gz file and serve that instead. Loosely based on GZipMiddleware"

    # TODO for hashed asset files, we should add a very long cache header: public, max-age=31536000, immutable
    # TODO should we assert against the three possible types we would expecvt here?

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
                    headers = GZIP_HEADERS

                    return FileResponse(
                        gz_path,
                        # FileResponse uses `guess_type` but falls back to `text/plain`, we mimic this behavior, but
                        # for the non-gzipped file
                        media_type=(content_type or "text/plain"),
                        headers=headers,
                    )

        return await super().get_response(path, scope)

        # TODO appartently AI thinks we should add these headers to non-gzip responses too, in case we end up
        # TODO however, I've never seen this error in the wild...
        # serving them as gzipped in the future... I need to investigate this more
        # response = await super().get_response(path, scope)

        # # ensure caches keep distinct representations per Accept-Encoding
        # try:
        #     response.headers.setdefault("Vary", "Accept-Encoding")
        # except Exception:
        #     # some responses may not have mutable headers; in that case just return as-is
        #     pass

        # return response


def mount_public_directory(app: FastAPI):
    # TODO should be extracted into another env var so it can be shared with JS
    if is_production() or is_staging():
        public_path = root / "public"
    else:
        public_path = root / "web/build" / python_environment() / "client"

    # in development, a separate py & js server will be used, if the development build DNE that's fine
    if not public_path.exists() and (is_development() or is_local_testing()):
        log.warning(
            "The development build does not exist. Static files will not be served",
            build_path=public_path,
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

    index_html_response = FileResponse(
        public_path / "index.html",
        # never cache this file, we want it to be pulled on every page load since it (a) is very small and (b) mostly
        # links out to other files, which we can safely cache
        headers=HTML_NOCACHE_HEADERS,
    )

    @app.get("/", include_in_schema=False)
    async def javascript_index():
        return index_html_response

    # TODO Assets with hashes: cache aggressively?
    # elif "/assets/" in str(fp) and any(char in fp.stem for char in ['-', '_']):  # Has hash
    #     headers = {
    #         "Cache-Control": "public, max-age=31536000, immutable",  # 1 year
    #     }
    #     return FileResponse(fp, headers=headers)

    @app.get("/{path:path}", include_in_schema=False)
    async def frontend_handler(path: str):
        """
        This is a very dangerous piece of code: if this is not last it will override other routes in the application

        Without this, non-index RR routes will not work. When a path is requested that does not exist in the fastapi
        application, it servers up the index.html file. Most likely, this path is a RR route.

        https://gist.github.com/ultrafunkamsterdam/b1655b3f04893447c3802453e05ecb5e
        """
        fp = public_path / path

        # react-router puts prerendered HTML routes into the `index.html` in directory name of the route requested
        # https://reactrouter.com/how-to/pre-rendering
        prerender_path = public_path / path / "index.html"
        if prerender_path.exists():
            return FileResponse(prerender_path)

        if not fp.exists():
            return index_html_response

        return FileResponse(fp)

    return app
