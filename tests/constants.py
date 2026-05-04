"""
Make sure this file does not depend on `app`.

This is why `environs` is used instead of our custom stricter env module.
"""

from environs import env

TMP_DIRECTORY = env.path("TMP_DIRECTORY")

# this entire folder is uploaded as an artifact
TEST_RESULTS_DIRECTORY = env.path("TEST_RESULTS_DIRECTORY")

PYTHON_TEST_SERVER_HOST = env.str("PYTHON_TEST_SERVER_HOST")

LONG_INTEGRATION_TEST_TIMEOUT = 15_000
"indicates that a particular part of a integration test may need a while to resolve"
