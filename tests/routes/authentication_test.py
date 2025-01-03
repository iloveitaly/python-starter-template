import os

import requests
from fastapi import status
from fastapi.testclient import TestClient

from app.server import api_app

from tests.utils import get_clerk_dev_user


def get_valid_token():
    _, _, user = get_clerk_dev_user()

    # now that we have a user, we need to create a session
    session_response = requests.post(
        "https://api.clerk.com/v1/sessions",
        headers={"Authorization": f"Bearer {os.environ['CLERK_PRIVATE_KEY']}"},
        json={"user_id": user.id},
    )

    session_id = session_response.json()["id"]

    token_response = requests.post(
        f"https://api.clerk.com/v1/sessions/{session_id}/tokens",
        headers={
            "Authorization": f"Bearer {os.environ['CLERK_PRIVATE_KEY']}",
            "Content-Type": "application/json",
        },
    )

    token_id = token_response.json()["jwt"]

    return token_id


def test_unauthorized_no_credentials(client: TestClient):
    response = client.get(api_app.url_path_for("application_data"))

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_authorized_bad_credentials(client: TestClient):
    response = client.get(
        api_app.url_path_for("application_data"),
        headers={"Authorization": "Bearer BAD_CREDS"},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_authorized_good_credentials(client: TestClient):
    token_id = get_valid_token()

    response = client.get(
        api_app.url_path_for("application_data"),
        headers={"Authorization": f"Bearer {token_id}"},
    )

    assert response.status_code == status.HTTP_200_OK
