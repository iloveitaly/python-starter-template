import pytest

from app.configuration.versions import _retry_while_unreachable


def test_retries_while_service_is_unreachable():
    attempts = []

    def flaky_probe():
        attempts.append(1)
        if len(attempts) == 1:
            raise OSError("nodename nor servname provided, or not known")
        return "8.0.0"

    assert _retry_while_unreachable(flaky_probe) == "8.0.0"
    assert len(attempts) == 2


def test_does_not_retry_a_broken_probe():
    attempts = []

    def broken_probe():
        attempts.append(1)
        raise KeyError("redis_version")

    with pytest.raises(KeyError):
        _retry_while_unreachable(broken_probe)

    assert len(attempts) == 1
