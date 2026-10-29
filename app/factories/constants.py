from app.env import loose_env

CLERK_DEV_USER_PASSWORD = "clerk-development-123"

CLERK_QA_USER_EMAIL = "qa+clerk_test@example.com"
"not used in the test suite, but used for dev login"

CLERK_DEV_USER_EMAIL = "user+clerk_test@example.com"
"plain old normal user"

CLERK_DEV_ADMIN_EMAIL = "admin+clerk_test@example.com"
"user with an admin role set locally"

CLERK_DEV_SEED_EMAIL = "seed+clerk_test@example.com"
"user with seed data attached"

CLERK_EXTRA_USERS_TO_PRESERVE = loose_env.list("CLERK_PRESERVED_USER_EMAILS", [])
"""
Comma-separated emails the test suite must not delete.

`delete_all_clerk_users` deletes every user on the Clerk dev instance that isn't preserved. CI and local
development usually share an instance, so a test run deletes users a developer created by hand. Set this
locally *and* as a `CLERK_PRESERVED_USER_EMAILS` repository variable, since CI also runs the cleanup.
"""

CLERK_ALL_USERS_TO_PRESERVE = [
    email.strip().lower()
    for email in [
        CLERK_DEV_USER_EMAIL,
        CLERK_DEV_ADMIN_EMAIL,
        CLERK_QA_USER_EMAIL,
        CLERK_DEV_SEED_EMAIL,
        *CLERK_EXTRA_USERS_TO_PRESERVE,
    ]
]
