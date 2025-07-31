"""
Using `python` for the filename would cause issues, so we use lang.

This file is meant to align python configuration options across versions to avoid
weird bugs between dev, prod, ci, etc.
"""

import multiprocessing
import os
import sys

from app.environments import is_production


def configure_python():
    """
    Linux vs macOS changes the default spawn method, which heavily impacts how the multiprocess module operates.

    Specifically, this impacts our integration tests. They succeed on linux (fork) and not on macos (spawn)
    """
    from app import log

    if "TZ" not in os.environ:
        log.warning("TZ not set, update your environment configuration")

    try:
        # this is not the default as of py 3.13 on all platforms, but `fork` is deprecated
        if (existing_start_method := multiprocessing.get_start_method()) != "spawn":
            # if this is set multiple times, it throws an exception without force=True
            # I could not determine what is setting the start method before me here
            multiprocessing.set_start_method("spawn", force=True)

            log.info(
                "multiprocessing set to spawn", existing_method=existing_start_method
            )
        else:
            log.info("multiprocessing already set to spawn")
    except RuntimeError as e:
        log.warning(
            "multiprocessing start method failed to set",
            error=e,
            existing_method=multiprocessing.get_start_method(),
        )

    if is_production() and "PYTHONBREAKPOINT" not in os.environ and sys.breakpointhook:
        sys.breakpointhook = None
        log.info("disabling python breakpoints in production environment")
