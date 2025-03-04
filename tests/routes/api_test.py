from fastapi import status
from fastapi.testclient import TestClient

from app.server import api_app

from app.models.user import User

from tests.routes.utils import get_valid_token


def test_unauthorized_no_credentials(client: TestClient):
    response = client.get(api_app.url_path_for("external_api_ping"))

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_authorized_bad_credentials(client: TestClient):
    response = client.get(
        api_app.url_path_for("external_api_ping"),
        headers={"Authorization": "Bearer BAD_CREDS"},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_authorized_clerk_credentials(client: TestClient):
    token_id = get_valid_token()

    response = client.get(
        api_app.url_path_for("external_api_ping"),
        headers={"Authorization": f"Bearer {token_id}"},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_authorized_api_credentials(client: TestClient):
    # TODO should use a factory
    user = User(clerk_id="user_123").save()
    user.generate_api_key()

    response = client.get(
        api_app.url_path_for("external_api_ping"),
        headers={"Authorization": f"Bearer {user.api_key}"},  # noqa: S104
    )

    assert response.status_code == status.HTTP_200_OK
