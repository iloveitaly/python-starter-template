import re


def assert_matches(regex, string):
    if not re.search(regex, string):
        raise AssertionError(f"Regex '{regex}' does not match the string '{string}'")
