"""
Provide an entrypoint for configuring development tooling to make life easier
"""

import sys

import beautiful_traceback

from app.env import env
from app.environments import is_productionish
from app.utils.lang import callable_file_line_reference


def configure_debugging():
    from app import log

    # set configuration to be used in prod when rendering JSON exceptions to the logs
    beautiful_traceback.configure(
        local_stack_only=env.bool("BEAUTIFUL_TRACEBACK_LOCAL_ONLY", False),
    )

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

    beautiful_traceback.install(
        # don't allow rich, or anyone else, to override our excepthook
        only_hook_if_default_excepthook=False,
    )

    # don't install these traps by default, they are generally just for debugging
    if env.bool("PYTHON_DEBUG_TRAPS", False):
        from app.utils.debug import install_traps

        install_traps()
