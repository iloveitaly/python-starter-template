import typing as t

import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

from tests.routes.utils import (
    MockAuthenticateRequest,
    base_server_url,
)


@pytest.fixture
def api_client():
    from app.server import api_app

    with TestClient(api_app, base_url="api.example.com") as client:
        yield client


@pytest.fixture
def client(faker):
    "client to connect to your fastapi routes"
    from app.server import api_app

    with TestClient(api_app, base_url=base_server_url()) as client:
        client.cookies.clear()
        # Set default IP for all tests using this client, without this `testclient` is the ip address
        # of `request.client.host` which is not a valid ipv4 or ipv6 address
        client.headers = {"x-forwarded-for": faker.ipv4()}
        yield client


@pytest.fixture
def authenticated_client():
    "mocks out the clerk authentication and returns a static response"

    from app.routes.internal import authenticate_clerk_request_middleware
    from app.server import api_app

    api_app.dependency_overrides[authenticate_clerk_request_middleware] = (
        MockAuthenticateRequest()
    )

    with TestClient(api_app, base_url=base_server_url()) as client:
        client.cookies.clear()
        yield client

    api_app.dependency_overrides = {}


@pytest.fixture
async def aclient() -> t.AsyncGenerator[AsyncClient, None]:
    from app.server import api_app

    async with AsyncClient(
        transport=ASGITransport(app=api_app),
        base_url=base_server_url(),
    ) as client:
        client.cookies.clear()
        yield client
