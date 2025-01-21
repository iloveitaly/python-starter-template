"""
Provide an entrypoint for configuring development tooling to make life easier
"""

from decouple import config

from app.environments import is_development, is_testing


def configure_debugging():
    if not is_development() and not is_testing():
        return

    # TODO can we prevent rich from installing syshook?

    try:
        import pretty_traceback

        pretty_traceback.install()
    except ImportError:
        pass

    if config("PYTHON_DEBUG_TRAPS", default=False, cast=bool):
        from app.utils.debug import install_traps

        install_traps()
