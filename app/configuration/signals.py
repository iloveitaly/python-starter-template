import faulthandler
import inspect
import os
import signal
from collections import defaultdict
from types import FrameType
from typing import Callable, Set

import structlog

log = structlog.get_logger()

_handlers: dict[int, list[Callable]] = defaultdict(
    list
)  # sig -> list of user-added handlers
_original_handlers: dict[int, Callable | int | None] = {}  # sig -> original handler
_installed: Set[int] = set()  # signals with chained handler installed


def add_handler(sig: int, handler: Callable[[int, FrameType | None], None]) -> None:
    if sig not in _installed:
        _install_chained_handler(sig)
    _handlers[sig].append(handler)
    log.debug(
        "added user handler for signal",
        signum=sig,
        signal_name=_signal_name(sig),
        sigcode=_sigcode(sig),
    )


def _install_chained_handler(sig: int) -> None:
    old_handler = signal.getsignal(sig)
    _log_existing_handler(sig, old_handler)
    _original_handlers[sig] = old_handler

    def chained_handler(signum: int, frame: FrameType | None) -> None:
        log.info(
            "received signal",
            signum=signum,
            signal_name=_signal_name(signum),
            sigcode=_sigcode(signum),
        )

        # Then original handler if applicable
        orig = _original_handlers.get(signum)
        if callable(orig):
            orig(signum, frame)
        elif (
            orig == signal.SIG_DFL
        ):  # SIG_DFL: default signal handler (typically terminates the process or performs OS-default action)
            signal.signal(signum, signal.SIG_DFL)
            os.kill(os.getpid(), signum)
            signal.signal(signum, chained_handler)  # Restore; unreached if terminating
        elif (
            orig == signal.SIG_IGN
        ):  # SIG_IGN: ignore the signal (do nothing when received)
            pass
        else:
            log.warning(
                "unhandled original signal handler",
                signal_name=_signal_name(signum),
                sigcode=_sigcode(signum),
                handler=orig,
            )
        # Then user-added handlers in order
        for user_handler in _handlers[signum]:
            user_handler(signum, frame)

    signal.signal(sig, chained_handler)
    _installed.add(sig)
    log.debug(
        "installed chained handler for signal",
        signum=sig,
        signal_name=_signal_name(sig),
        sigcode=_sigcode(sig),
    )


def _log_existing_handler(sig: int, old_handler: Callable | int | None) -> None:
    if old_handler in (
        signal.SIG_DFL,
        signal.SIG_IGN,
    ):  # SIG_DFL: default handler; SIG_IGN: ignore signal
        return

    log.info(
        "modifying existing handler for signal",
        signum=sig,
        signal_name=_signal_name(sig),
        sigcode=_sigcode(sig),
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
                signal_name=_signal_name(sig),
                sigcode=_sigcode(sig),
                error=error,
                old_handler=old_handler,
            )


def _signal_name(signum: int) -> str:
    """Return a clean signal name without any trailing numeric suffix.

    Some platforms may format the string as "Name: 28"; strip the numeric suffix.
    """
    text = signal.strsignal(signum) or ""

    head, sep, tail = text.rpartition(":")
    if sep and tail.strip().isdigit():
        return head.strip()

    return text


def _sigcode(signum: int) -> str:
    return signal.Signals(signum).name


def configure_signals() -> None:
    catchable_sigs = set(signal.Signals) - {
        signal.SIGKILL,  # Kill (cannot be caught or ignored)
        signal.SIGSTOP,  # Stop (cannot be caught or ignored)
        signal.SIGINT,  # Interrupt (usually Ctrl+C)
        signal.SIGCHLD,  # Child process terminated, noisy
    }

    if faulthandler.is_enabled():
        catchable_sigs -= {
            signal.SIGSEGV,  # Segmentation fault (invalid memory access)
            signal.SIGFPE,  # Floating point exception (e.g., divide by zero)
            signal.SIGABRT,  # Abort (from abort() or assert failure)
            signal.SIGBUS,  # Bus error (misaligned memory access)
            signal.SIGILL,  # Illegal instruction
        }

    for sig in catchable_sigs:
        _install_chained_handler(sig)

    log.info("installed signal handlers")
