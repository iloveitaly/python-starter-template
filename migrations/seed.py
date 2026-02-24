"""
Seed development, test, and preview databases with data that is mostly realistic.

- This is only file outside of tests/ that should import from that module (factories, constants, etc).
- Will refuse to run in production or staging.
- This file is excluded from pyright, so it's not imported from.
- `--safe` option exists to only run if the DB is empty. This is helpful when running automatically (via `just dev`) to
  avoid accidentally clobbering data or cluttering the database.

TODO can we detect if database state does not match the latest model configuration?
"""

if __name__ != "__main__":
    raise RuntimeError(
        "This module should only be executed directly and should not be imported."
    )

import argparse
import sys

from app import log
from app.configuration.database import is_database_empty
from app.environments import is_production, is_staging

from app.models.user import User

from tests.routes.utils import get_clerk_seed_user


def check_safe_seeding():
    """
    Check if database is completely empty and is absolutely safe to seed
    """

    parser = argparse.ArgumentParser(description="Seed the database with data.")
    parser.add_argument(
        "--safe",
        action="store_true",
        help="Only run seeding if all tables are empty",
    )
    args = parser.parse_args()

    if args.safe and not is_database_empty():
        log.warning(
            "skipping seeding because --safe was passed and database is not empty"
        )
        sys.exit(0)


if is_production() or is_staging():
    raise RuntimeError("seed.py must never run in production or staging")

check_safe_seeding()

try:
    _, _, clerk_user = get_clerk_seed_user()
    user = User.find_or_create_by(clerk_id=clerk_user.id)
except Exception as e:
    log.error("error creating clerk user, most likely a clerk authentication issue")
    log.exception(e)  # type: ignore

log.info("seed complete")
