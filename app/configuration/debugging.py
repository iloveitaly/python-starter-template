"""
Provide an entrypoint for configuring development tooling to make life easier
"""

from app.environments import is_development, is_testing


def configure_debugging():
    if not is_development() and not is_testing():
        return

    try:
        import pretty_traceback

        pretty_traceback.install()
    except ImportError:
        pass
