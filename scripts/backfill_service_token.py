"""
Phase 3: Backfill - Copy api_key -> service_token for existing rows.

Run once after deploying Phase 2 (dual-write).
Idempotent: safe to run multiple times.

Usage:
    uv run python scripts/backfill_service_token.py
"""

if __name__ != "__main__":
    raise RuntimeError("This script should only be run directly")

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app import log
from app.environments import is_production, is_staging
from app.models.user import User


def backfill_service_token() -> int:
    count = 0

    users = User.where(
        User.api_key.is_not(None),
        User.service_token.is_(None),
    ).all()

    for user in users:
        user.service_token = user.api_key  # type: ignore
        user.save()
        count += 1
        log.info("backfilled user", user_id=user.id)

    return count


if is_production() or is_staging():
    confirm = input("Running in prod/staging. Type 'yes' to continue: ")
    if confirm != "yes":
        log.info("aborted")
        sys.exit(1)

updated = backfill_service_token()
log.info("backfill complete", total_updated=updated)
