from fastapi import status
from fastapi.testclient import TestClient

from app.generated.fastapi_typed_routes import api_app_url_path_for

from app.models.user import User

from tests.routes.clerk import get_valid_token


def test_unauthorized_no_credentials(client: TestClient):
    response = client.get(
        api_app_url_path_for("external_api_ping_external_v1_ping_get")
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_authorized_bad_credentials(client: TestClient):
    response = client.get(
        api_app_url_path_for("external_api_ping_external_v1_ping_get"),
        headers={"Authorization": "Bearer BAD_CREDS"},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_authorized_no_bearer(client: TestClient):
    response = client.get(
        api_app_url_path_for("external_api_ping_external_v1_ping_get"),
        headers={"Authorization": "BAD_CREDS"},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_authorized_clerk_credentials(client: TestClient):
    token_id = get_valid_token()

    response = client.get(
        api_app_url_path_for("external_api_ping_external_v1_ping_get"),
        headers={"Authorization": f"Bearer {token_id}"},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_authorized_api_credentials(client: TestClient):
    # TODO should use a factory
    user = User(clerk_id="user_123").save()
    user.generate_api_key()

    response = client.get(
        api_app_url_path_for("external_api_ping_external_v1_ping_get"),
        headers={"Authorization": f"Bearer {user.api_key}"},
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "ok"}
