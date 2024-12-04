"""
Using `python` for the filename would cause issues, so we use lang.

This file is meant to align python configuration options across versions to avoid
weird bugs between dev, prod, ci, etc.
"""

import multiprocessing


def configure_python():
    # this is not the default as of py 3.13 on all platforms, but `fork` is deprecated
    multiprocessing.set_start_method("spawn")
