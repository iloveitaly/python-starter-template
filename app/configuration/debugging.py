"""
Provide an entrypoint for configuring development tooling to make life easier
"""

from app.environments import is_development


def configure_debugging():
    if not is_development():
        return

    try:
        import pretty_traceback

        pretty_traceback.install()
    except ImportError:
        pass
