# this wasn't working, foreman reported as false but also raw python was false
# simple tty wasn't enough either
# I think pydub has something fancy they do to detect this...

    # TODO curious if this properly reports under foreman, etc
    # still reports TTY inside foreman...
    import sys

    if sys.stdin.isatty():
        print("Running in interactive mode, enabling debugging tools")
    else:
        print("Running in non-interactive mode, disabling debugging tools")

    def is_stdin_interactive():
        from select import select

        # Check if stdin is a TTY
        if not sys.stdin.isatty():
            return False

        # Check if stdin has data available (non-blocking)
        r, _, _ = select([sys.stdin], [], [], 0.1)
        return bool(r)  # Returns True if stdin is readable

    if is_stdin_interactive():
        print("Running in interactive mode, enabling debugging tools")
    else:
        print("Running in non-interactive mode, disabling debugging tools")
