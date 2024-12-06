"""
Using `python` for the filename would cause issues, so we use lang.

This file is meant to align python configuration options across versions to avoid
weird bugs between dev, prod, ci, etc.
"""

import multiprocessing


def configure_python():
    """
    Linux vs macOS changes the default spawn method, which heavily impacts how the multiprocess module operates
    """
    from app import log

    try:
        # this is not the default as of py 3.13 on all platforms, but `fork` is deprecated
        if (existing_start_method := multiprocessing.get_start_method()) != "spawn":
            # if this is set multiple times, it throws an exception
            # I could not determine what is setting the start method before me here
            multiprocessing.set_start_method("spawn", force=True)

            log.info(
                "multiprocessing set to spawn", existing_method=existing_start_method
            )
        else:
            log.info("multiprocessing already set to spawn")
    except RuntimeError as e:
        log.warning(f"multiprocessing start method failed to set: {e}")
