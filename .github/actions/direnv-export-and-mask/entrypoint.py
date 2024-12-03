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
    # Base64-like strings of significant length
    re.compile(r"^[A-Za-z0-9+/]{32,}={0,2}$"),
    # UUID-like strings
    re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"),
    # Common secret prefixes
    re.compile(r"^(key-|api-|token-|secret-|private-).*"),
    # High entropy strings
    re.compile(r"[A-Za-z0-9+/]{40,}"),
    # Common API key formats
    re.compile(r"api_[A-Za-z0-9]{32,}"),
    re.compile(r"key-[0-9a-zA-Z]{32,}"),
]

# Define suffixes to detect keys to mask
key_suffixes = [
    "_KEY",
    "_TOKEN",
    "_SECRET",
    "_PASSWORD",
    "_DSN",
    "_API_KEY",
    "_PRIVATE_KEY",
    "_SIGNING_KEY",
    "_ACCESS_KEY",
]


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
