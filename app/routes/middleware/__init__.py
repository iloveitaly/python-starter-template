from decouple import config
from fastapi import FastAPI
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app import log
from app.environments import is_development

from . import access_log, logging

SESSION_SECRET_KEY = config("SESSION_SECRET_KEY", cast=str)

ALLOWED_HOST_LIST = config("ALLOWED_HOST_LIST", cast=str)
"""
This is a very important configuration option:

- Used to block requests that don't have a `Host:` header that matches this list
- Determines which hosts cookies are set for
"""


def allowed_hosts(with_scheme: bool = False) -> list[str]:
    """
    Returns a list of allowed hosts, with or without scheme.

    Development hosts are automatically added.
    """

    DEVELOPMENT_HOSTS = [
        "127.0.0.0",
        "0.0.0.0",
        "localhost",
    ]

    hosts = [host.strip() for host in ALLOWED_HOST_LIST.split(",")]
    assert hosts

    if with_scheme:
        hosts = [f"https://{host}" for host in hosts]

    if is_development():
        if with_scheme:
            # don't force https for devs who aren't using localias
            hosts.extend(
                [f"http://{host}" for host in DEVELOPMENT_HOSTS if host not in hosts]
            )
        else:
            hosts.extend(DEVELOPMENT_HOSTS)

    return hosts


def add_middleware(app: FastAPI):
    """
    Entrypoint to add all middleware for the root router:

    - Not requiring HTTPS here since it is assumed we'll be behind a proxy server
    - Looks like middleware is processed outside in, so the order here is important
    """

    access_log.add_middleware(app)

    # this adds `context`, which access logs require
    logging.add_middleware(app)

    # CORS require that a specific scheme is used for the request
    allowed_hosts_with_schemes = allowed_hosts(True)

    log.info("allowed_origins", allowed_origins=allowed_hosts_with_schemes)

    # even in development, CORS is required, especially since we are using separate domains for API & frontend
    # `http OPTIONS https://web.localhost` to test configuration here
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_hosts_with_schemes,
        # tells browsers to expose and include credentials (such as cookies, client-side certificates, and authorization headers) in cross-origin requests.
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # trusted hosts are not required for development, but reduces delta between prod & dev
    # include the API host in your trusted host list, this will be used as the `Host` when HTTP/2 is used (which does
    # not specify the `Host` header explicitly, it's inferred from `:authority` pseudo-header)
    allowed_hosts_without_scheme = allowed_hosts(False)
    app.add_middleware(
        TrustedHostMiddleware, allowed_hosts=allowed_hosts_without_scheme
    )

    cookie_domain = allowed_hosts_without_scheme[0]
    log.info("cookie_domain", cookie_domain=cookie_domain)

    # note that `domain_cookie` and `https_only` will cause issues if you are not using
    # domains + localias (for local https) for testing. If cookie-related route + integration tests
    # fail, this code is probably to blame.
    # https://www.starlette.io/middleware/#sessionmiddleware
    app.add_middleware(
        SessionMiddleware,
        secret_key=SESSION_SECRET_KEY,
        https_only=True,
        domain=cookie_domain,
        # same_site="Lax", is defined by default
    )

    if is_development() and config("FASTAPI_DEBUG", cast=bool, default=False):
        from app.utils.debug import PdbMiddleware

        # TODO should conditionally include this dependending on set_trace, and fix the stdin/stdout
        # app.add_middleware(PdbrMiddleware, debug=True)

        app.add_middleware(PdbMiddleware, debug=True)

    return app
