"""

If a structlog contextvar approach is used, it's possible for context to be lost since fastapi/starlette
can run threaded, forked, and async code. I don't claim to fully understand exactly *why* starlette-context
is needed, and it's possible that it's not needed at all at this point.

References:

- https://pypi.org/project/fastapi-structlog/0.5.0/ (https://github.com/iloveitaly/fastapi-logger)
- https://pypi.org/project/asgi-correlation-id/ - used to generate a request ID that is added to all logs
- https://gist.github.com/nymous/f138c7f06062b7c43c060bf03759c29e
- https://github.com/sharu1204/fastapi-structlog/blob/master/app/main.py - old implementation
- https://github.com/tomwojcik/starlette-context
"""

from time import perf_counter

import sentry_sdk
from decouple import config
from fastapi import FastAPI
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import RequestResponseEndpoint
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Match, Mount
from starlette.types import Scope
from starlette_context import context, plugins
from starlette_context.header_keys import HeaderKeys
from starlette_context.middleware import RawContextMiddleware

from app import log
from app.environments import is_development


def add_middleware(app: FastAPI):
    @app.middleware("http")
    async def sentry_transaction_id_middleware(
        request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # https://github.com/snok/asgi-correlation-id/blob/ed006dcc119447bf68a170bd1557f6015427213d/asgi_correlation_id/extensions/sentry.py#L18-L33
        # https://blog.sentry.io/trace-errors-through-stack-using-unique-identifiers-in-sentry/
        scope = sentry_sdk.get_isolation_scope()
        scope.set_tag("transaction_id", context[HeaderKeys.request_id])
        return await call_next(request)

    app.add_middleware(
        RawContextMiddleware,
        plugins=(plugins.RequestIdPlugin(),),
    )
