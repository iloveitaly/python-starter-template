from fastapi import status

from app.generated.fastapi_typed_routes import api_app_url_path_for

from tests.assertions import assert_status


def test_example_payment_pending_rejects_unknown_session_id(client):
    response = client.post(
        api_app_url_path_for("create_example_payment_pending"),
        json={
            "stripe_checkout_session_id": "not-a-session",
            "email": "buyer@example.com",
        },
    )

    assert_status(response, status.HTTP_400_BAD_REQUEST)
    assert response.json()["error"]["message"] == "Invalid checkout session"


def test_example_payment_pending_rejects_payment_intent_id(client):
    response = client.post(
        api_app_url_path_for("create_example_payment_pending"),
        json={
            "stripe_checkout_session_id": "pi_3RPofKPNRRX3VZhd0CHUAjEi",
            "email": "buyer@example.com",
        },
    )

    assert_status(response, status.HTTP_400_BAD_REQUEST)
    assert response.json()["error"]["message"] == "Invalid checkout session"


def test_example_payment_complete_rejects_unknown_session_id(client):
    response = client.get(
        api_app_url_path_for("complete_example_payment"),
        params={"session_id": "not-a-session"},
    )

    assert_status(response, status.HTTP_400_BAD_REQUEST)
    assert response.json()["error"]["message"] == "Invalid checkout session"
