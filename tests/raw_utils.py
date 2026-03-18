"""
Raw utilities that do not depend on any application code or other test modules.
These functions are safe to import and use before the environment is fully initialized
or before the app module is loaded.
"""

import sys

from termcolor import colored


def banner(text, color="red", file=sys.__stderr__, flush=True):
    # Split text into lines, preserving empty lines, but strip leading/trailing newlines
    lines = text.strip("\n").split("\n")

    if not lines:
        return

    width = max((len("# " + line) for line in lines), default=0)

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
