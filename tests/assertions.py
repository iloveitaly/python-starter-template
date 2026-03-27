import re

from fastapi import status


def assert_matches(regex, string):
    if not re.search(regex, string):
        raise AssertionError(f"Regex '{regex}' does not match the string '{string}'")


def assert_status(response, status_code: int = status.HTTP_200_OK):
    assert response.status_code == status_code, (
        f"{response.status_code}: {response.json()}"
    )


def assert_main_server_config_is_stable():
    """
    Assert that the server configuration in main.py hasn't changed.
    If it has, we need to verify if tests/integration/subprocess_server.py needs updates.
    """
    from app.utils.patching import hash_function_code
    from main import get_server_config

    expected_hash = "8ffa786c74c8a426fabb9b695889b6d3ad4d2b465249c0f06716171098ef0b50"
    actual_hash = hash_function_code(get_server_config)

    assert actual_hash == expected_hash, (
        f"main.py config has changed. New hash: {actual_hash}. "
        "If this was intentional, update the expected hash in tests/assertions.py "
        "and verify if tests/integration/subprocess_server.py also needs updates."
    )
