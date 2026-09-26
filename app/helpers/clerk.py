"""
Get-or-create helpers for Clerk users, and the local `User` records linked to them.
"""

from collections.abc import Callable
from functools import wraps

import httpx
from clerk_backend_api import User as ClerkUser
from clerk_backend_api.models import ClerkBaseError

from app import log
from app.configuration.clerk import clerk

from app.models.user import User


def safely_execute_clerk[**P, R](func: Callable[P, R]) -> Callable[P, R | None]:
    "Ensure clerk calls that a user interaction blocks on fail gracefully, returning `None` instead of a 500"

    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R | None:
        try:
            return func(*args, **kwargs)
        except ClerkBaseError, httpx.RequestError:
            log.exception("clerk call failed", function=func.__name__)
            return None

    return wrapper


def clerk_user_exists(email: str) -> bool:
    """Whether a Clerk account already exists for this email."""

    users = clerk.users.list(request={"email_address": [email]})
    return bool(users)


def get_or_create_clerk_user(email: str, *, password: str | None = None) -> ClerkUser:
    """Return the Clerk user for the given email, creating it if necessary."""

    users = clerk.users.list(request={"email_address": [email]})

    if users and len(users) == 1:
        return users[0]

    if not users:
        if password is None:
            created = clerk.users.create(email_address=[email])
        else:
            created = clerk.users.create(email_address=[email], password=password)

        assert created
        return created

    # multiple users with same email, this should never happen
    raise ValueError("more than one clerk user found for email")


def get_or_create_user_from_email(email: str) -> User:
    """
    Resolve a local `User` for an email address, creating both the Clerk account and the
    linked `User` record if either is missing. Idempotent: safe to call repeatedly for the
    same email, e.g. once a streaming order or API request has an email but no user yet.
    """

    clerk_user = get_or_create_clerk_user(email)

    user = User.find_or_create_by(clerk_id=clerk_user.id)
    if not user.email:
        user.email = email
    user.save()

    log.info(
        "ensured clerk-backed user for email",
        user_id=user.id,
        clerk_id=user.clerk_id,
    )

    return user
