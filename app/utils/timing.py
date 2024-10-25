import functools
from contextlib import ContextDecorator
from time import perf_counter

from .. import log


# TODO there's got to be a package to do this for us, we can just hot-swap it out later
# https://stackoverflow.com/questions/33987060/python-context-manager-that-measures-time
class log_execution_time(ContextDecorator):
    """
    Usage:
    ```
    with log_execution_time('description'):
        # Your code here...
    ```
    """

    def __init__(self, msg=None):
        """
        :param msg: message to log, normally a function name
        """

        self.msg = msg

    def __enter__(self):
        self.time = perf_counter()
        return self

    # NOTE exit is still called even if an exception is raised
    def __exit__(self, _type, _value, _traceback):
        elapsed = perf_counter() - self.time

        # NOTE this assumes flow_sdk logger with accepts structured logging dict
        log.debug(
            f"{self.msg} took {elapsed:.3f} seconds",
            {
                "execution_time": elapsed,
                "function_name": self.msg,
            },
        )


def log_time(msg=None):
    def decorator(func):
        function_name = func.__name__

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with log_execution_time(msg or function_name):
                return func(*args, **kwargs)

        return wrapper

    return decorator
