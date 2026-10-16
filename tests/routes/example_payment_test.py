from fastapi import status

from app.generated.fastapi_typed_routes import api_app_url_path_for

from tests.assertions import assert_status


def test_example_payment_pending_rejects_invalid_client_secret(client):
    response = client.post(
        api_app_url_path_for("create_example_payment_pending"),
        json={"client_secret": "not-a-secret"},
    )

    assert_status(response, status.HTTP_400_BAD_REQUEST)
    assert response.json()["error"]["message"] == "Invalid client secret"


def test_example_payment_pending_rejects_payment_intent_client_secret(client):
    response = client.post(
        api_app_url_path_for("create_example_payment_pending"),
        json={
            "client_secret": "pi_3RPofKPNRRX3VZhd0CHUAjEi_secret_aRC74awl3qM01aWWqSDDF8t1r"
        },
    )

    assert_status(response, status.HTTP_400_BAD_REQUEST)
    assert (
        response.json()["error"]["message"]
        == "Invalid checkout session ID in client secret"
    )
