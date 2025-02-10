from decouple import config
from fastapi import FastAPI
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.environments import is_development
from app.routes.dependencies.timing import add_timing_middleware
from app.server import is_production

SESSION_SECRET_KEY = config("SESSION_SECRET_KEY", cast=str)
ALLOWED_HOST_LIST = config("TRUSTED_HOST_LIST", cast=str)


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

    # not required for development, but reduces delta between prod & dev
    allowed_hosts = [host.strip() for host in ALLOWED_HOST_LIST.split(",")]
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)

    app.add_middleware(
        SessionMiddleware, secret_key=SESSION_SECRET_KEY, https_only=is_production()
    )

    add_timing_middleware(app)

    if is_development() and config("FASTAPI_DEBUG", cast=bool, default=False):
        from app.utils.debug import PdbMiddleware

        # TODO should conditionally include this dependending on set_trace, and fix the stdin/stdout
        # app.add_middleware(PdbrMiddleware, debug=True)

        app.add_middleware(PdbMiddleware, debug=True)

    return app
