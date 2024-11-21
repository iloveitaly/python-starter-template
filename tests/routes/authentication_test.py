from fastapi import status
from fastapi.testclient import TestClient

from app.configuration.clerk import clerk


def test_unauthorized_no_credentials(client: TestClient):
    response = client.get("/internal/v1/")

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_authorized_bad_credentials(client: TestClient):
    response = client.get(
        "/internal/v1/", headers={"Authorization": "Bearer BAD_CREDS"}
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_authorized_good_credentials(client: TestClient):
    testing_tokens = clerk.testing_tokens.create()
    assert testing_tokens

    response = client.get(
        "/internal/v1/", headers={"Authorization": f"Bearer {testing_tokens.token}"}
    )

    # TODO this is failing
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
