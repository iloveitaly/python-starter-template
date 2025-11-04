"""
Provide an entrypoint for configuring development tooling to make life easier
"""

import types

from decouple import config

from app.environments import is_production, is_staging


class VariableLoggingModule(types.ModuleType):
    """
    Helpful class to help determine when a particular field is overridden by tracing when an attribute is set.

    >>> sys.__class__ = VariableLoggingModule
    """

    def __setattr__(self, name, value):
        if name == "excepthook":
            import inspect

            frame = inspect.currentframe().f_back
            filename = frame.f_code.co_filename
            lineno = frame.f_lineno
            function_name = frame.f_code.co_name
            print(
                f"Logging: excepthook overridden at {filename}:{lineno} in {function_name}"
            )
        super().__setattr__(name, value)


def configure_debugging():
    if is_production() or is_staging():
        return

    # TODO can we prevent rich from installing syshook?
    # TODO can we detect if excepthook has been mutated?

    # if sys.excepthook != sys.__excepthook__:
    #     print(
    #         f"sys.excepthook has been overridden by {sys.excepthook.__module__}.{sys.excepthook.__qualname__}"
    #     )
    #     print(
    #         f"Source: {getattr(sys.excepthook, '__code__', None) and sys.excepthook.__code__.co_filename}:{getattr(sys.excepthook, '__code__', None) and sys.excepthook.__code__.co_firstlineno}"
    #     )
    #     # raise RuntimeError("sys.excepthook has been overridden.")

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

    if config("PYTHON_DEBUG_TRAPS", default=False, cast=bool):
        from app.utils.debug import install_traps

        install_traps()
