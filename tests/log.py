"""
This is a very lonely file, intentionally.

If any of the core application is loaded before mutating the environment, it can cause
the current process (and someprocesses, in some cases!) to not pick up on the updates.

For this reason, we have a very simple logger setup here so the rest of the test
utilities can easily import it and use it throughout the codebase without worrying about
importing the rest of the application.
"""

import structlog

# named logger for all test-specific logic to use
log = structlog.get_logger(logger_name="test")
