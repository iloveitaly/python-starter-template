"""
Exercise FastAPI's synchronous and asynchronous route handling beyond Python's
recursion limit.

Both endpoints are intentionally requested in the same loop so FastAPI's
synchronous and asynchronous route paths share the same evolving router state.

The motivating incident behind this test was a fastapi upgrade which changed
how sync routes were handled in a way that caused the Sentry library to continue
re-wrapping route methods, eventually causing a permanent production failure.

The most generalized version of that failure is just hitting the sync endpoint
more times than the recursion limit, in case there is some state mutation issue
which accumulates over time.

https://github.com/getsentry/sentry-python/issues/6568
"""

import sys

from app.generated.fastapi_typed_routes import api_app_url_path_for

from tests.assertions import assert_status


def test_fastapi_routes_survive_recursion_limit(client):
    paths = [
        api_app_url_path_for(name)
        for name in ("unauthenticated_ping", "unauthenticated_aping")
    ]

    for _ in range(sys.getrecursionlimit() + 1):
        for path in paths:
            assert_status(client.get(path))
