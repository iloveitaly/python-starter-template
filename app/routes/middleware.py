from fastapi import FastAPI
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware.cors import CORSMiddleware

from app.routes.dependencies.timing import add_timing_middleware


def add_middleware(app: FastAPI):
    # even in development, some sort of CORS is required
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # NOTE we are intentionally not requiring HTTPS here since it is assumed we'll be behind a proxy server
    # TODO TrustedHostMiddleware?

    add_timing_middleware(app)

    return app
