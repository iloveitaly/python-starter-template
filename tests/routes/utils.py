import os

import requests

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
