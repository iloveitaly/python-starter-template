import re

from fastapi import FastAPI
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from structlog_config import fastapi_access_logger

from app import log
from app.env import env
from app.environments import is_development

from . import logging_context

SESSION_SECRET_KEY = env.str("SESSION_SECRET_KEY")

ALLOWED_HOST_LIST = env.str("ALLOWED_HOST_LIST")
"""
This is a very important configuration option:

- Used to block requests that don't have a `Host:` header that matches this list
- Determines which hosts cookies are set for (first one in the list!)
"""

DEVELOPMENT_HOSTS = [
    "127.0.0.1",
    "::1",
    "localhost",
]
"""
0.0.0.0 is a bind address only adn is not used by browsers, which is why it's excluded
"""


def allowed_hosts(with_scheme: bool = False) -> list[str]:
    """
    Returns a list of allowed hosts for this service.

    - When `with_scheme=True`, production hosts are prefixed with `https://`.
      In development, known development hosts are prefixed with `http://` to
      match typical local setups and CORS expectations.
    - When `with_scheme=False`, bare hostnames are returned.
    - Common development hosts are automatically added when running in development.

    This function is used by:

    - CORS configuration (origins must include scheme and, for dev, may include ports)
    - Trusted host protection (FastAPI `TrustedHostMiddleware`)
    - Session/cookie domain selection (the first host in the list)

    Notes:

    - `ALLOWED_HOST_LIST` must contain bare hostnames only (no scheme, no path).
      If an entry begins with `http://`, it will be ignored and a warning logged.
    - Local development servers often run on arbitrary ports; CORS handling augments these
      values with a regex to allow any port for development hosts.
    """

    raw_hosts = [host.strip() for host in ALLOWED_HOST_LIST.split(",")]

    hosts_without_scheme: list[str] = []
    for host in raw_hosts:
        if not host:
            continue

        # only HTTPS is allowed; ignore any http:// entries
        if host.lower().startswith("http://") or host.lower().startswith("https://"):
            log.warning(
                "scheme provided in ALLOWED_HOST_LIST, ignoring host", host=host
            )
            continue

        hosts_without_scheme.append(host)

    assert hosts_without_scheme, "at least a single allowed host is required"

    if is_development():
        hosts_without_scheme.extend(DEVELOPMENT_HOSTS)

    if not with_scheme:
        return list(dict.fromkeys(hosts_without_scheme))

    # production hosts default to https; development hosts default to http in dev
    def with_correct_scheme(h: str) -> str:
        if is_development() and h in DEVELOPMENT_HOSTS:
            return f"http://{h}"
        return f"https://{h}"

    hosts_with_scheme = [with_correct_scheme(host) for host in hosts_without_scheme]

    # keep order stable but remove duplicates
    return list(dict.fromkeys(hosts_with_scheme))


def add_middleware(app: FastAPI):
    """
    Entrypoint to add all middleware for the root router:

    - Not requiring HTTPS here since it is assumed we'll be behind a proxy server
    - Looks like middleware is processed outside in, so the order here is important
    """

    # replace the default fastapi logger with something nicer
    fastapi_access_logger.add_middleware(app)

    # this adds `context`, which access logs require
    logging_context.add_middleware(app)

    # CORS require that a specific scheme is used for the request
    allowed_hosts_with_schemes = allowed_hosts(True)

    # In development, browsers include the dynamic port in the Origin for local servers
    # (e.g. Vite, Playwright, etc.). Since we don't know the port, allow any port for
    # known development hosts via a regex while still enumerating explicit origins.
    allow_origin_regex: str | None = None
    if is_development():
        dev_hosts_pattern = "|".join(re.escape(h) for h in DEVELOPMENT_HOSTS)
        allow_origin_regex = rf"^http://(?:{dev_hosts_pattern})(?::\\d+)?$"

    log.info("allowed_origins", allowed_origins=allowed_hosts_with_schemes)

    # even in development, CORS is required, especially since we are using separate domains for API & frontend
    # `http OPTIONS https://web.localhost` to test configuration here
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_hosts_with_schemes,
        allow_origin_regex=allow_origin_regex,
        # tells browsers to expose and include credentials (such as cookies, client-side certificates, and authorization headers) in cross-origin requests.
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # trusted hosts are not required for development, but reduces delta between prod & dev
    # include the API host in your trusted host list, this will be used as the `Host` when HTTP/2 is used (which does
    # not specify the `Host` header explicitly, it's inferred from `:authority` pseudo-header)
    # when this check fails, you'll get a plain "Invalid host header" response with a 400 status code. No logs.
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

    if is_development() and env.bool("FASTAPI_DEBUG", False):
        from app.utils.debug import PdbMiddleware

        # TODO should conditionally include this dependending on set_trace, and fix the stdin/stdout
        # app.add_middleware(PdbrMiddleware, debug=True)

        app.add_middleware(PdbMiddleware, debug=True)

    return app
