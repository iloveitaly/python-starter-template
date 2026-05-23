"""
Raw utilities that do not depend on any application code or other test modules.
These functions are safe to import and use before the environment is fully initialized
or before the app module is loaded.
"""

import shutil
import sys
from pathlib import Path

from termcolor import colored

_TESTS_ROOT = Path(__file__).parent


def banner(text, color="red", file=sys.__stderr__, flush=True):
    # Split text into lines, preserving empty lines, but strip leading/trailing newlines
    lines = text.strip("\n").split("\n")

    if not lines:
        return

    message_width = max((len("# " + line) for line in lines), default=0)
    terminal_width = shutil.get_terminal_size(fallback=(80, 24)).columns
    width = min(message_width, terminal_width)

    print(colored("#" * width, color), file=file, flush=flush)
    for line in lines:
        parts = line.split("`")
        formatted_line = ""
        for i, part in enumerate(parts):
            if i % 2 == 1:
                # This part is inside backticks
                formatted_line += colored(f"`{part}`", "light_blue")
            else:
                formatted_line += colored(part, color)

        print(colored("# ", color) + formatted_line, file=file, flush=flush)
    print(colored("#" * width, color), file=file, flush=flush)


def autoload_pytest_plugins_list(folder: str | Path) -> list[str]:
    """Return a list suitable for assigning to `pytest_plugins`.

    Relative paths are resolved against the tests/ directory. The dotted
    package name is inferred from the path relative to the project root.

    Example:
        pytest_plugins = autoload_pytest_plugins_list("plugins")
    """
    folder = Path(folder)
    if not folder.is_absolute():
        folder = (_TESTS_ROOT / folder).resolve()

    package = ".".join(folder.relative_to(_TESTS_ROOT.parent).parts)

    return [
        f"{package}.{p.stem}"
        for p in sorted(folder.glob("*.py"))
        if p.stem != "__init__" and not p.stem.startswith("_")
    ]
