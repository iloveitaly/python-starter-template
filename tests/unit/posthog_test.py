import posthog
import pytest

from app.configuration.posthog import posthog_client


def test_default_client_is_the_configured_instance():
    assert posthog.default_client is posthog_client
    assert posthog_client.enable_exception_autocapture is False


def test_new_context_does_not_capture_exceptions_when_autocapture_is_disabled(mocker):
    capture = mocker.patch("posthog.capture_exception")

    with pytest.raises(RuntimeError, match="boom"):
        with posthog.new_context():
            raise RuntimeError("boom")

    capture.assert_not_called()
