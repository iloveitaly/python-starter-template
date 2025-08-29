"""
Custom errors for the application should go here
"""


class ImpossibleStateError(Exception):
    """
    Raised when an impossible state is encountered. By definition, this should never happen.

    It's useful to have as a distinct exception type to make (a) them easier to identify in Sentry and (b)
    self-document the case in-code.
    """

    pass
