"""
Provide an entrypoint for configuring development tooling to make life easier
"""

import sys

from decouple import config

from app.environments import is_productionish
from app.utils.lang import callable_file_line_reference


def configure_debugging():
    from app import log

    if is_productionish():
        return

    # TODO can we prevent rich from installing syshook?

    log.warning("configure_debugging")

    if sys.excepthook != sys.__excepthook__:
        source_reference = callable_file_line_reference(sys.excepthook)

        log.warning(
            "sys.excepthook has been overridden, this may interfere with debugging tools",
            excepthook_source_file=source_reference,
        )

    try:
        import beautiful_traceback

        beautiful_traceback.install(
            local_stack_only=config(
                "BEAUTIFUL_TRACEBACK_LOCAL_ONLY", default=False, cast=bool
            ),
            # don't allow rich, or anyone else, to override our excepthook
            only_hook_if_default_excepthook=False,
        )
    except ImportError:
        pass

    # don't install these traps by default, they are generally just for debugging
    if config("PYTHON_DEBUG_TRAPS", default=False, cast=bool):
        from app.utils.debug import install_traps

        install_traps()
