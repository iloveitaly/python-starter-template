from decouple import config
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.environments import is_development
from app.routes.dependencies.timing import add_timing_middleware


def add_middleware(app: FastAPI):
    """
    Entrypoint to add all middleware for the root router:

    - Not requiring HTTPS here since it is assumed we'll be behind a proxy server
    """
    # even in development, some sort of CORS is required
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    add_timing_middleware(app)

    if is_development() and config("FASTAPI_DEBUG", cast=bool, default=False):

        from app.utils.debug import PdbMiddleware

        # app.add_middleware(PdbrMiddleware, debug=True)
        app.add_middleware(PdbMiddleware, debug=True)

    return app
