"""
Should not be used in production. Helpful debugging tools for async code and other things.
"""


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

    import memray
    import time
    import sys

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
