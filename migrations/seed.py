"""
Seed fresh development and test databases with data.

This is only file outside of tests/ that should import from that module (factories, constants, etc).

Safeguards: will refuse to run in production or staging.

TODO can we hint to VSC not to pull symbols from this file?
TODO can we detect if database state does not match the latest model configuration?
"""

if __name__ != "__main__":
    raise RuntimeError(
        "This module should only be executed directly and should not be imported."
    )

from app.environments import is_production, is_staging

if is_production() or is_staging():
    raise RuntimeError("seed.py must never run in production or staging")

from app.models.user import User

from tests.routes.utils import get_clerk_seed_user

_, _, clerk_user = get_clerk_seed_user()
user = User.find_or_create_by(clerk_id=clerk_user.id)
