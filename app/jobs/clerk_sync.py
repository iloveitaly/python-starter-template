"""
Loop through all Users in our DB, retrieve the associated Clerk user,
and update the User record's email column from the Clerk data.
"""

from app import log
from app.celery import celery_app
from app.configuration.clerk import clerk

from app.models.user import User


def perform() -> None:
    """
    Perform the syncing of User email addresses with Clerk user data.
    """

    # TODO support deleted flag in clerk

    for user in User.all():
        try:
            clerk_user = clerk.users.get(user_id=user.clerk_id)
        except Exception:
            log.warning("no clerk user found for user", user=user)
            continue

        assert clerk_user

        if not clerk_user.email_addresses:
            log.warning("no email addresses found for clerk user", user=user)
            continue

        if len(clerk_user.email_addresses) > 1:
            log.info("multiple email addresses found for clerk user", user=user)

        user_email = clerk_user.email_addresses[0].email_address

        user.email = user_email
        user.save()

    log.info("users synced with clerk")


perform_celery = celery_app.task(perform)


def queue():
    "always use this method to queue jobs so it's easy to swap out the job system"
    perform_celery.delay()
