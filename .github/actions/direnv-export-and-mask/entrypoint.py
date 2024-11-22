import json
import re
import sys

# Define the patterns to match specific types of values
patterns = [
    re.compile(r"sk-\S+"),  # Matches sk-* values
    re.compile(
        r"https://\S+@o\d+\.ingest\.us\.sentry\.io/\S+"
    ),  # Matches the Sentry DSN pattern
    re.compile(r"sk_\S+"),  # Matches sk_* values
    re.compile(r"phc_\S+"),  # Matches phc-* values
]

# Define suffixes to detect keys to mask
key_suffixes = ["_KEY", "_TOKEN", "_SECRET", "_PASSWORD", "_DSN"]


def add_mask(value):
    print(f"::add-mask::{value}")


# Read JSON from stdin
env_vars = json.load(sys.stdin)

# Iterate over all variables from JSON input
for key, value in env_vars.items():
    # Check if the value matches any of the defined patterns
    if any(pattern.match(str(value)) for pattern in patterns):
        add_mask(str(value))
        continue

    # Check if the key ends with any of the defined suffixes
    if any(key.endswith(suffix) for suffix in key_suffixes):
        add_mask(str(value))
        continue

    # Check if the key starts with OP_ or DIRENV_
    if key.startswith("OP_") or key.startswith("DIRENV_"):
        add_mask(str(value))
