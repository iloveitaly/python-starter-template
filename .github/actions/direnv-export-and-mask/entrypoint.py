import argparse
import json
import re
import sys

parser = argparse.ArgumentParser()
parser.add_argument(
    "--all",
    type=lambda x: x.lower() == "true",
    default=False,
    help="Mask all environment variables",
)
args = parser.parse_args()

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

# prefixes & suffixes are case insensitive

# Define suffixes to detect keys to mask
key_suffixes = [
    "_KEY",
    "_TOKEN",
    "_SECRET",
    "_PASSWORD",
    "_DSN",
]

# Define prefixes to detect keys to mask
key_prefixes = ["OP_", "DIRENV_", "key-", "api-", "token-", "secret-", "private-"]


def add_mask(key, value):
    print("Masking key:", key)
    print(f"::add-mask::{value}")


def is_safe_value(value):
    common_words = [
        "test",
        "production",
        "staging",
        "dev",
        "test",
        "local",
        "localhost",
        "example.com",
        "postgres",
        "username",
        "password",
        ".",
        "true",
        "false",
    ]

    if any(word == value.lower() for word in common_words):
        return False

    # is this a 4 digit number or less? This generally represents a port
    if str(value).isdigit() and len(value) <= 4:
        return False

    return True


# Read JSON from stdin
env_vars = json.load(sys.stdin)

# Iterate over all variables from JSON input
for key, value in env_vars.items():
    # empty values are intentionally not skipped and will result in a mask warning
    # empty ENV values should be rare and should be loud if they are

    # Convert key to uppercase for comparison
    key_upper = key.upper()

    if (
        any(pattern.match(str(value)) for pattern in patterns)
        or any(key_upper.endswith(suffix.upper()) for suffix in key_suffixes)
        or any(key_upper.startswith(prefix.upper()) for prefix in key_prefixes)
    ):
        add_mask(key, str(value))
        continue

    if args.all:
        if is_safe_value(str(value)):
            print("Key value is safe, not masking.", key)
        else:
            print("Key not masked by default, masking because of --all.", key)
            add_mask(key, str(value))
