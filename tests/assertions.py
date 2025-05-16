import re

from fastapi import status


def assert_matches(regex, string):
    if not re.search(regex, string):
        raise AssertionError(f"Regex '{regex}' does not match the string '{string}'")


def assert_status(response, status_code: int = status.HTTP_200_OK):
    assert response.status_code == status_code, response.json()
