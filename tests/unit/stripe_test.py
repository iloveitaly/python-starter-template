import pytest

from app.lib.stripe import (
    extract_checkout_session_id_from_client_secret,
    extract_payment_intent_id_from_client_secret,
)
from app.routes.errors import ClientError


def test_extract_payment_intent_id_from_client_secret_success():
    client_secret = "pi_3RPofKPNRRX3VZhd0CHUAjEi_secret_aRC74awl3qM01aWWqSDDF8t1r"
    assert (
        extract_payment_intent_id_from_client_secret(client_secret)
        == "pi_3RPofKPNRRX3VZhd0CHUAjEi"
    )


def test_extract_payment_intent_id_from_client_secret_invalid():
    with pytest.raises(ClientError) as exc_info:
        extract_payment_intent_id_from_client_secret("")
    assert exc_info.value.status_code == 400
    assert exc_info.value.code == "BAD_REQUEST"

    with pytest.raises(ClientError) as exc_info:
        extract_payment_intent_id_from_client_secret("invalid_secret")
    assert exc_info.value.status_code == 400

    with pytest.raises(ClientError) as exc_info:
        extract_payment_intent_id_from_client_secret("notpi_123_secret_456")
    assert exc_info.value.status_code == 400


def test_extract_checkout_session_id_from_client_secret_success():
    client_secret = "cs_test_a1tQWKwHJ9fMYVL2TjkDDqX2qvvnKnI3zb5dw3exS1wb0TXvEjwVxXKmzo_secret_fidwbEhqYWAnPydmcHZxamgneCUl"
    assert (
        extract_checkout_session_id_from_client_secret(client_secret)
        == "cs_test_a1tQWKwHJ9fMYVL2TjkDDqX2qvvnKnI3zb5dw3exS1wb0TXvEjwVxXKmzo"
    )


def test_extract_checkout_session_id_from_client_secret_invalid():
    with pytest.raises(ClientError) as exc_info:
        extract_checkout_session_id_from_client_secret("")
    assert exc_info.value.status_code == 400

    with pytest.raises(ClientError) as exc_info:
        extract_checkout_session_id_from_client_secret("cs_invalid")
    assert exc_info.value.status_code == 400

    with pytest.raises(ClientError) as exc_info:
        extract_checkout_session_id_from_client_secret("notcs_123_secret_456")
    assert exc_info.value.status_code == 400
