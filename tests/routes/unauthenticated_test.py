from fastapi import status

from app.server import api_app


async def test_https_redirection(aclient):
    response = await aclient.get(api_app.url_path_for("healthcheck"))

    assert response.status_code == status.HTTP_200_OK
