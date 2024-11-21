from typing import AsyncGenerator

import pytest
from decouple import config
from fastapi import status
from httpx import ASGITransport, AsyncClient

from app.server import api_app


# https://github.com/zhanymkanov/fastapi-best-practices?tab=readme-ov-file#set-tests-client-async-from-day-0
@pytest.fixture
async def aclient() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=api_app),
        base_url=config("VITE_PYTHON_URL", cast=str),
    ) as client:
        yield client


@pytest.mark.asyncio
async def test_https_redirection(client):
    response = client.get(api_app.url_path_for("healthcheck"))

    assert response.status_code == status.HTTP_200_OK
