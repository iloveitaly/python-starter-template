export PYTHON_ENV=test
export NODE_ENV=test

# One the tricky aspects of a test environment is integration tests
# we want these to run as closely to the production environment as possible
# this means HTTPS support and using production-build javascript.
#
# However, When running tests locally we want to:
#
#   * Use a separate database
#   * Use a separate domain so we can run a local server in parallel
#   * Because a separate domain is used, we'll need to use a different report
#     and change the domain used by the javascript client.

# the react router generator from py requires this to generate a full url
export BASE_URL="https://${PYTHON_TEST_SERVER_HOST}"

export VITE_PYTHON_URL="https://${PYTHON_TEST_SERVER_HOST}"

# in test, the javascript is served off of the python server, like production
export VITE_APP_BASE_URL="https://${PYTHON_TEST_SERVER_HOST}"

# additional arguments you want to always set on pytest
# export PYTEST_ADDOPTS='--arg example '
