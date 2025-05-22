"""
Seed fresh development and test databases with data.

This is only file outside of tests/ that should import from that module (factories, constants, etc).
"""

from app.models.user import User

from tests.routes.utils import get_clerk_seed_user

_, _, clerk_user = get_clerk_seed_user()
user = User.find_or_create_by(clerk_id=clerk_user.id)
