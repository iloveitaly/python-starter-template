import faulthandler
import inspect
import os
import signal

import structlog

log = structlog.get_logger()


def log_existing_handler(sig, old_handler):
    """Log details if modifying an existing signal handler."""
    # SIG_DFL: default signal handler (usually terminates process)
    if old_handler in (signal.SIG_DFL, signal.SIG_IGN):
        return

    log.info(
        "modifying existing handler for signal",
        signum=sig,
        signal=signal.strsignal(sig),
    )

    if callable(old_handler):
        try:
            file = inspect.getfile(old_handler)
            line = inspect.getsourcelines(old_handler)[1]
            log.info("existing handler source", file=file, line=line)
        except (OSError, TypeError) as error:
            log.info(
                "could not retrieve source location for handler of signal",
                signum=sig,
                signal=signal.strsignal(sig),
                error=error,
                old_handler=old_handler,
            )


def add_signal_handler(sig, new_handler):
    """
    Add a new handler for the signal while chaining to the existing one.

    Logs if overriding an existing handler and attempts to preserve original behavior.
    """
    old_handler = signal.getsignal(sig)
    log_existing_handler(sig, old_handler)

    def chained_handler(signum, frame):
        new_handler(signum, frame)  # Execute new handler first
        if callable(old_handler):
            old_handler(signum, frame)
        # SIG_DFL: default signal handler (usually terminates process)
        elif old_handler == signal.SIG_DFL:
            signal.signal(signum, signal.SIG_DFL)
            os.kill(os.getpid(), signum)
            signal.signal(signum, chained_handler)  # Restore; unreached if terminating
        # SIG_IGN is handled by doing nothing
        elif old_handler == signal.SIG_IGN:
            pass
        else:
            log.warning(
                "unhandled signal handler",
                signal=signal.strsignal(sig),
                handler=old_handler,
            )

    signal.signal(sig, chained_handler)
    log.debug(
        "installed logging handler for signal",
        signum=sig,
        signal=signal.strsignal(sig),
    )


def log_handler(signum, frame):
    """Log the received signal."""
    log.info(
        "received signal",
        signum=signum,
        signal=signal.strsignal(signum),
    )


def configure_signals():
    # Exclude uncatchable signals
    catchable_sigs = set(signal.Signals) - {
        # SIGKILL: cannot be caught or ignored (force kill)
        signal.SIGKILL,
        # SIGSTOP: cannot be caught or ignored (force stop)
        signal.SIGSTOP,
        # SIGINT: interrupt signal (Ctrl+C), there's a default python handler for this
        signal.SIGINT,
    }

    if faulthandler.is_enabled():
        # avoids logging around these signals already being caught, etc
        catchable_sigs -= {
            signal.SIGSEGV,
            signal.SIGFPE,
            signal.SIGABRT,
            signal.SIGBUS,
            signal.SIGILL,
        }

    for sig in catchable_sigs:
        add_signal_handler(sig, log_handler)

    log.info("installed signal handlers")
