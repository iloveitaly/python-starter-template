import json
import logging
import re
import sys

# Define the patterns to match specific types of values
patterns = [
    re.compile(r"sk-\S+"),  # Matches sk-* values
    re.compile(
        r"https://\S+@o\d+\.ingest\.us\.sentry\.io/\S+"
    ),  # Matches the Sentry DSN pattern
    re.compile(r"sk_\S+"),  # Stripe & other keys
    re.compile(r"phc_\S+"),  # PostHog token
    re.compile(r"sntrys_\S+"),  # Sentry auth token
]

# Define suffixes to detect keys to mask
key_suffixes = ["_KEY", "_TOKEN", "_SECRET", "_PASSWORD", "_DSN"]


def add_mask(key, value):
    print("Masking key:", key)
    print(f"::add-mask::{value}")


# Read JSON from stdin
env_vars = json.load(sys.stdin)

# Iterate over all variables from JSON input
for key, value in env_vars.items():
    # Skip empty values with warning
    if not str(value).strip():
        logging.warning(f"Skipping masking for empty value in key: {key}")
        continue

    if any(pattern.match(str(value)) for pattern in patterns) or any(
        key.endswith(suffix) for suffix in key_suffixes
    ):
        add_mask(key, str(value))
        continue

    # Check if the key starts with OP_ or DIRENV_
    if key.startswith("OP_") or key.startswith("DIRENV_"):
        add_mask(key, str(value))
