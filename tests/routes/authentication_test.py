import os
import time

import requests
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


def get_valid_token():
    timestamp = int(time.time())

    user = clerk.users.create(
        request={
            "email_address": [f"user-{timestamp}+clerk_test@example.com"],
            "password": "clerk-development-123",
        }
    )

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


def test_authorized_good_credentials(client: TestClient):
    token_id = get_valid_token()

    response = client.get(
        "/internal/v1/", headers={"Authorization": f"Bearer {token_id}"}
    )

    assert response.status_code == status.HTTP_200_OK
