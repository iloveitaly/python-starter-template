from app.env import env

CLERK_DEV_USER_PASSWORD = "clerk-development-123"

CLERK_QA_USER_EMAIL = "qa+clerk_test@example.com"
"not used in the test suite, but used for dev login"

CLERK_DEV_USER_EMAIL = "user+clerk_test@example.com"
"plain old normal user"

CLERK_DEV_ADMIN_EMAIL = "admin+clerk_test@example.com"
"user with an admin role set locally"

CLERK_DEV_SEED_EMAIL = "seed+clerk_test@example.com"
"user with seed data attached"

CLERK_ALL_USERS_TO_PRESERVE = [
    CLERK_DEV_USER_EMAIL,
    CLERK_DEV_ADMIN_EMAIL,
    CLERK_QA_USER_EMAIL,
    CLERK_DEV_SEED_EMAIL,
]

TMP_DIRECTORY = env.path("TMP_DIRECTORY")

# this entire folder is uploaded as an artifact
TEST_RESULTS_DIRECTORY = env.path("TEST_RESULTS_DIRECTORY")

PYTHON_TEST_SERVER_HOST = env.str("PYTHON_TEST_SERVER_HOST")

LONG_INTEGRATION_TEST_TIMEOUT = 15_000
"indicates that a particular part of a integration test may need a while to resolve"
