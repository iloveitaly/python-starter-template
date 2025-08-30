from fastapi import status
from fastapi.testclient import TestClient

from app.server import api_app

from tests.routes.utils import bearer_headers, get_valid_token


def test_unauthorized_no_credentials(client: TestClient):
    response = client.get(api_app.url_path_for("application_data"))

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_authorized_bad_credentials(client: TestClient):
    response = client.get(
        api_app.url_path_for("application_data"),
        headers=bearer_headers("BAD_CREDS"),
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_authorized_good_credentials(client: TestClient):
    token_id = get_valid_token()
    assert token_id

    response = client.get(
        api_app.url_path_for("application_data"),
        headers=bearer_headers(token_id),
    )

    assert response.status_code == status.HTTP_200_OK
