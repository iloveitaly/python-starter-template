# NOTE: rename to `.env.dev.local` and customize for your local development preferences

# https://github.com/microsoft/pylance-release/blob/8a9161449fb8a2076f19681dabc3b7c93c7de1d7/USING_WITH_PYRIGHT.md?plain=1#L9
export PYRIGHT_PYTHON_PYLANCE_VERSION=latest-release

# export LOG_LEVEL=DEBUG
# export PYTHONDEVMODE=1

# extremely noisy, but helpful in a pinch
# export PYTHONVERBOSE=1

# log raw SQL which is executed
# export ACTIVEMODEL_LOG_SQL=true

# dev mode enables asyncio debug
# export PYTHONASYNCIODEBUG=1

# debug pytest internals
# export PYTEST_DEBUG=1

# redirect logs to a file for inspection
# export PYTHON_LOG_PATH=

# change the default breakpoint tooling
# export PYTHONBREAKPOINT=pdbr.set_trace
# export PYTHONBREAKPOINT=ipdb.celery_set_trace
# export PYTHONBREAKPOINT=pudb.set_trace
# export PYTHONBREAKPOINT=pdb.set_trace
# export PYTHONBREAKPOINT=ipdb.set_trace
# can deal with forked processes
# export PYTHONBREAKPOINT=pudb.forked.set_trace
# useful when the process is forked and stdin is not connected to a tty (fastapi dev, etc) and stdout is overloaded
# export PYTHONBREAKPOINT=rpdb.set_trace

# export IPDB_CONTEXT_SIZE

# run playwright in headful mode, can also use --headed on pytest CLI
# https://github.com/microsoft/playwright-python/blob/c4df71cb9cf653622c1aa7b02ed874f2fae3feb1/tests/conftest.py#L50
# export HEADFUL=1

# exposes a `playwright` global object into the chromium devtools
# https://playwright.dev/docs/debug#browser-developer-tools
# export PWDEBUG=console

# enable pdbr fastapi middleware to catch exceptions inside of fastapi
# export FASTAPI_DEBUG=1

# installs USR1 and USR2 signals to enable debugging for async and threaded bugs
# export PYTHON_DEBUG_TRAPS=1

# enables very verbose low-level playwright logs. There is no way to redirect these to a specific file.
# you should avoid using DEBUG for anything in the application-layer as many node packages end up using this ENV
# var for debugging. https://github.com/microsoft/playwright/issues/6465
# export DEBUG=pw:api

# or, if you need extreme verbosity
# export DEBUG=pw:*
# https://github.com/microsoft/playwright-python/issues/1782
# export DEBUG_FILE="tmp/playwright_debug.log"

# shorter stack with only local frames
# export PRETTY_TRACEBACK_LOCAL_ONLY=True

# suppress or expand py warnings
# export PYTHONWARNINGS=""
export PYTHONWARNINGS="ignore::DeprecationWarning,ignore:ResourceWarning"

# not standard python, but used in many libraries. Adds color to output.
# NO_COLOR is used to control our application logging color
export PY_COLORS=1
# export NO_COLOR=1

# debugging a trace mise issue?
# export MISE_LOG_LEVEL=trace

# debugging a nixpacks/docker issue and want to consume the raw logs?
# export BUILDKIT_PROGRESS=plain

# add paths to override default tooling, helpful when hacking on a cli dependency
# note that this can be problematic if you have binaries which override with mise. Mise will most likely force its
# bin/ dirs for those binaries first.
# PATH_add ~/Projects/go/localias/bin/
# PATH_add ~/Projects/deployment/nixpacks/target/release/

# casing is important on openai level
# export OPENAI_LOG=debug
export LOG_LEVEL=info
export VITE_LOG_LEVEL=info
