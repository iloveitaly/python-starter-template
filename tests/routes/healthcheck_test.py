"""
TODO why async? mostly to test async client tests
"""

from fastapi import status

from app.server import api_app


async def test_healthcheck(aclient):
    response = await aclient.get(api_app.url_path_for("healthcheck"))

    assert response.status_code == status.HTTP_200_OK


async def test_user_status(aclient):
    response = await aclient.get(api_app.url_path_for("active_user_status"))

    # should error since there are no users
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
