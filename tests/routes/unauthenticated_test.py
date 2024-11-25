from typing import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

from app.server import api_app
from tests.conftest import base_server_url

# TODO move to conftest once we understand this further
# justification is async DB connections will cause event loop issues, but that doesn't seem right
# https://github.com/zhanymkanov/fastapi-best-practices?tab=readme-ov-file#set-tests-client-async-from-day-0


@pytest.fixture
async def aclient() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=api_app),
        base_url=base_server_url(),
    ) as client:
        yield client


# @pytest.mark.asyncio
# async def test_https_redirection(aclient):
#     response = await aclient.get(api_app.url_path_for("healthcheck"))

#     assert response.status_code == status.HTTP_200_OK
