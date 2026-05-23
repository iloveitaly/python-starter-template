"""
Using `python` for the filename would cause issues, so we use lang.

This file is meant to align python configuration options across versions to avoid
weird bugs between dev, prod, ci, etc.
"""

import multiprocessing
import sys
import time
from pathlib import Path

from app.env import loose_env
from app.environments import is_macos, is_production


def install_system_certificates():
    """
    Make Python's TLS stack trust the macOS keychain.

    Why: Locally-installed root CAs (OrbStack, mkcert, corporate MITM
    proxies) live in the macOS keychain. Python's `ssl` module and
    everything built on it (`requests`, `httpx`, `urllib3`, `aiohttp`)
    ignore the keychain and verify against certifi's bundled roots, so
    `requests.get("https://x.orb.local")` fails with SSLCertVerificationError
    even though curl and the browser work fine.

    Why not env vars: `REQUESTS_CA_BUNDLE` *replaces* certifi rather than
    merging, so it requires a hand-maintained union bundle that goes stale
    on every certifi upgrade. `SSL_CERT_FILE` is read by Go, Ruby, libcurl,
    and more — setting it in your shell breaks TLS across your whole
    toolchain if the bundle ever has a problem. Both are ambient state
    affecting every process in the shell, not just code that needs it.

    Why truststore: Wraps macOS Security.framework in an `ssl.SSLContext`,
    monkey-patches `ssl` so every TLS library in *this process* uses the
    keychain. No env vars, no bundle, no blast radius. New keychain roots
    work immediately. It's the default HTTPS verifier in pip 24.2+.

    On Linux this is a no-op — stdlib already uses OpenSSL's default paths,
    which is what truststore would fall back to anyway.

    Call once at startup, before any library caches an SSLContext.
    """
    if not is_macos():
        return

    import truststore

    truststore.inject_into_ssl()


def configure_python():
    """
    Linux vs macOS changes the default spawn method, which heavily impacts how the multiprocess module operates.

    Specifically, this impacts our integration tests. They succeed on linux (fork) and not on macos (spawn)
    """
    from app import log

    install_system_certificates()
    inspect_python_runtime()

    # prefer intentional timezone configuration
    if loose_env.str("TZ") is None:
        log.warning("TZ not set, update your environment configuration")

    # prefer UTC for consistent server behavior
    if time.timezone != 0 or time.daylight != 0:
        log.warning(
            "timezone not UTC",
            tzname=time.tzname,
            timezone=time.timezone,
            daylight=time.daylight,
        )

    try:
        # this is not the default as of py 3.13 on all platforms, but `fork` is deprecated
        if (existing_start_method := multiprocessing.get_start_method()) != "spawn":
            # if this is set multiple times, it throws an exception without force=True
            # I could not determine what is setting the start method before me here
            multiprocessing.set_start_method("spawn", force=True)

            log.info(
                "multiprocessing set to spawn", existing_method=existing_start_method
            )
        else:
            log.info("multiprocessing already set to spawn")
    except RuntimeError as e:
        log.warning(
            "multiprocessing start method failed to set",
            error=e,
            existing_method=multiprocessing.get_start_method(),
        )

    if (
        is_production()
        and loose_env.str("PYTHONBREAKPOINT") is None
        and sys.breakpointhook
    ):
        sys.breakpointhook = None
        log.info("disabling python breakpoints in production environment")


def inspect_python_runtime() -> None:
    """
    Run some runtime checks to alert on some rare-but-hard-to-debug issues.

    - Check if the Python interpreter is running in a virtual environment.
    - Check if the interpreter is the global/system Python. For instance, VSC extensions will attempt to create a
      venv with the system Python vs the mise python.

    If not, log a warning with environment details.
    """

    from app import log

    executable = Path(sys.executable).resolve()

    # is set by virtualenv (not venv) to the original prefix
    real_prefix = getattr(sys, "real_prefix", None)

    in_venv = (
        real_prefix is not None
        or sys.base_prefix != sys.prefix
        or loose_env.str("VIRTUAL_ENV") is not None
    )

    if not in_venv:
        env_var_keys = ["VIRTUAL_ENV", "PATH", "PYTHONPATH"]
        env_vars = {key: loose_env.str(key) for key in env_var_keys}

        log.warning(
            "not using a virtual environment",
            interpreter=executable,
            real_prefix=real_prefix,
            env=env_vars,
            sys_path=sys.path,
            # root directory of the current Python installation (e.g., /usr/local for system Python or /path/to/venv for virtual env)
            prefix=sys.prefix,
            # original base installation prefix (system-wide Python's prefix) in venv environments (equals sys.prefix outside venvs)
            base_prefix=sys.base_prefix,
        )
    else:
        log.debug(
            "virtual environment detected", interpreter=executable, venv=sys.prefix
        )

    # TODO there are probably other keywords we should test for
    if in_venv and ("homebrew" in str(executable) or "/usr/bin/" in str(executable)):
        log.error(
            "using venv, but interpreter is from an unexpected location",
            interpreter=executable,
        )
