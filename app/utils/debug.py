# type: ignore

"""
Should not be used in production. Helpful debugging tools for async code and other things.

Types are ignored since not all of the packages are included as dependencies
"""

import traceback
from contextlib import contextmanager
from logging import Logger

from app import log


def install_coroutine_trap():
    """
    Listen to USR1 signal to dump all coroutine state to the console.

    kill -USR1 <pid>

    Helpful for debugging deadlocks
    """

    import asyncio
    import os
    import signal
    import sys

    def dump_all_tasks(sig, frame):
        all_tasks = asyncio.all_tasks()

        print(f"dump all tasks ({len(all_tasks)}) stack trace", file=sys.stderr)

        for task in all_tasks:
            try:
                name = task.get_name()
                print(f"task {name}:", file=sys.stderr)
                asyncio.Task.print_stack(task, file=sys.stderr)
            except Exception as e:
                print(f"error dumping task: {e}", file=sys.stderr)

    signal.signal(signal.SIGUSR1, dump_all_tasks)

    print(f"installed USR1 signal handler on pid {os.getpid()}", file=sys.stderr)


def install_thread_trap():
    """
    Listen to USR2 signal to dump all thread state to the console.

    kill -USR2 <pid>

    Helpful for debugging deadlocks
    """

    import os
    import signal
    import sys

    def dump_all_threads(sig, frame):
        for thread_id, stack in sys._current_frames().items():
            print(f"Thread {thread_id}:", file=sys.stderr)
            for filename, lineno, name, line in traceback.extract_stack(stack):
                print(f"  File: {filename}, line {lineno}, in {name}", file=sys.stderr)
                if line:
                    print(f"    {line.strip()}", file=sys.stderr)

    signal.signal(signal.SIGUSR2, dump_all_threads)

    print(f"installed USR2 signal handler on pid {os.getpid()}", file=sys.stderr)


@contextmanager
def scalene_profile():
    import time

    from scalene import scalene_profiler
    from scalene.scalene_profiler import Scalene

    timestamp = int(time.time())
    output_file = f"scalene_{timestamp}.bin"

    # all available options: https://github.com/plasma-umass/scalene/blob/6e07aeba241b156ed2378cbd7d4f4fdd586d36ea/scalene/scalene_arguments.py#L38
    # https://github.com/plasma-umass/scalene/blob/6e07aeba241b156ed2378cbd7d4f4fdd586d36ea/scalene/scalene_profiler.py#L1854
    # Scalene.__output.output_file = output_file
    Scalene._Scalene__output = output_file

    # Scalene._Scalene__args.profile_interval = 60
    # Scalene._Scalene__next_output_time = time.perf_counter() + Scalene._Scalene__args.profile_interval

    scalene_profiler.start()

    yield

    scalene_profiler.stop()


@contextmanager
def memray_profile(log: Logger | None = None, live: bool = False):
    """
    Not for use in production, only for local memory leak debugging.

    `live` allows you to watch memory allocations in a separate terminal:

        memray live 12345

    Most of the time, you want to avoid doing live tracking to (a) allow fork tracking and (b) output tracking to a file

      https://github.com/bloomberg/memray/discussions/585
    """

    import sys
    import time

    import memray

    if live:
        live_socket = memray.SocketDestination(12345, "0.0.0.0")

        # NOTE follow_fork does not seem to work with live
        # > --follow-fork mode can only be used with an output file. It is incompatible with --live mode and --live-remote mode, since the TUI can’t be attached to multiple processes at once.

        tracker_args = {
            "destination": live_socket,
            "follow_fork": False,
            "native_traces": True,
        }
    else:
        # if a unique file name is not used an exception will be thrown
        timestamp = int(time.time())
        file_name = "playground/memray/" + f"memray_{timestamp}.bin"
        tracker_args = {
            "file_name": file_name,
            "follow_fork": True,
            "native_traces": True,
        }

    if log:
        log.warn("starting memray tracker", tracker_args)
    else:
        print("starting memray tracker", file=sys.stderr)

    with memray.Tracker(**tracker_args):
        yield

    if log:
        log.warn("memory tracing complete")
    else:
        print("memory tracing complete", file=sys.stderr)
        print("memory tracing complete", file=sys.stderr)
        print("memory tracing complete", file=sys.stderr)


def log_system_options():
    log.info("system options", **dump_system_options())


def dump_system_options():
    options = {}

    # 1. Threading Stack Size
    import threading

    options["threading_stack_size"] = threading.stack_size()

    # 2. Garbage Collection Settings
    import gc

    options["gc_enabled"] = gc.isenabled()
    options["gc_thresholds"] = gc.get_threshold()
    options["gc_debug_flags"] = gc.get_debug()

    # 3. Recursion Limit
    import sys

    options["recursion_limit"] = sys.getrecursionlimit()

    # 4. Interpreter Optimization Flags
    options["optimization_flags"] = sys.flags.optimize

    # 5. Signal Handling
    import signal

    options["signal_handlers"] = {
        sig: signal.getsignal(getattr(signal, sig))
        for sig in dir(signal)
        if sig.startswith("SIG") and "_" not in sig
    }

    # 6. Environment Variables
    import os

    options["environment_variables"] = dict(os.environ)

    # 7. Locale Settings
    import locale

    options["locale"] = locale.getlocale()

    # 8. Asyncio Event Loop Policy
    try:
        import asyncio

        policy = asyncio.get_event_loop_policy()
        options["asyncio_event_loop_policy"] = type(policy).__name__
        loop = asyncio.get_event_loop()
        options["asyncio_debug"] = loop.get_debug()
    except ImportError:
        options["asyncio_event_loop_policy"] = None
        options["asyncio_debug"] = None

    # 9. Default Encoding
    options["default_encoding"] = sys.getdefaultencoding()

    # 10. Logging Configuration
    import logging

    logger = logging.getLogger()
    options["logging_level"] = logging.getLevelName(logger.getEffectiveLevel())

    # 11. Decimal Context
    import decimal

    context = decimal.getcontext()
    options["decimal_context"] = {
        "prec": context.prec,
        "rounding": context.rounding,
        "Emin": context.Emin,
        "Emax": context.Emax,
        "capitals": context.capitals,
        "flags": dict(context.flags),
        "traps": dict(context.traps),
    }

    # 12. Resource Limits (Unix only)
    try:
        import resource

        limits = {}
        for limit in dir(resource):
            if limit.startswith("RLIMIT"):
                soft, hard = resource.getrlimit(getattr(resource, limit))
                limits[limit] = {"soft": soft, "hard": hard}
        options["resource_limits"] = limits
    except (ImportError, AttributeError):
        options["resource_limits"] = None

    # 13. Global Exception Handling
    options["excepthook"] = sys.excepthook

    # 14. Thread Switch Interval
    options["thread_switch_interval"] = sys.getswitchinterval()

    # 15. Warnings Filter
    import warnings

    options["warnings_filters"] = warnings.filters.copy()

    # Additional Options:

    # 16. Faulthandler Status
    import faulthandler

    options["faulthandler_enabled"] = faulthandler.is_enabled()

    # 17. Tracemalloc Status
    import tracemalloc

    options["tracemalloc_tracing"] = tracemalloc.is_tracing()

    # 18. Coroutine Origin Tracking Depth
    options["coroutine_origin_tracking_depth"] = (
        sys.get_coroutine_origin_tracking_depth()
    )

    # 19. Async Generator Hooks
    options["asyncgen_hooks"] = sys.get_asyncgen_hooks()

    # 20. Audit Hooks
    options["audit_hooks"] = "Cannot retrieve audit hooks directly"

    # 21. Unraisable Exception Hook
    options["unraisablehook"] = sys.unraisablehook

    # 22. Dynamic Loading Flags
    if hasattr(sys, "getdlopenflags"):
        options["dlopen_flags"] = sys.getdlopenflags()
    else:
        options["dlopen_flags"] = None

    # 23. Hash Randomization Seed
    options["hash_randomization"] = sys.flags.hash_randomization

    # 24. Threading Exception Hook
    options["threading_excepthook"] = threading.excepthook

    # 25. Integer String Conversion Limits
    if hasattr(sys, "get_int_max_str_digits"):
        options["int_max_str_digits"] = sys.get_int_max_str_digits()
    else:
        options["int_max_str_digits"] = None

    # 26. Bytecode Generation Control
    options["dont_write_bytecode"] = sys.dont_write_bytecode

    # 27. Trace Function
    options["trace_function"] = sys.gettrace()

    # 28. Context Variables
    import contextvars

    options["contextvars"] = contextvars.copy_context()

    # 29. GC Debug Flags
    options["gc_debug_flags"] = gc.get_debug()

    # 30. PYTHONWARNINGS Environment Variable
    options["PYTHONWARNINGS"] = os.environ.get("PYTHONWARNINGS", None)

    return options
