"""
Redact credentials before they reach Sentry or stdout.

Meta's Conversions API SDK sends the access token as a query parameter and
interpolates that full URL into exception text. The same string then shows up
in stack locals (`url`) and in the exception message structlog prints.
"""

import re

FILTERED_SECRET = "[Filtered]"

# bare token stored under this key, as in FacebookAdsApi.init(access_token=...)
_SECRET_DICT_KEYS = frozenset({"access_token"})

_ACCESS_TOKEN_QUERY_PARAMETER = re.compile(
    r"""
    (access_token=)  # keep the parameter name so the request is still recognizable
    [^&\s]+          # value runs until the next query delimiter or whitespace
    """,
    re.VERBOSE,
)


def scrub_access_token(value: str) -> str:
    "replace `access_token=<secret>` query values with a filtered marker"

    return _ACCESS_TOKEN_QUERY_PARAMETER.sub(rf"\1{FILTERED_SECRET}", value)


def scrub_sentry_event(event: dict[str, object], _hint: object) -> dict[str, object]:
    """
    `before_send` / `before_send_transaction` hook.

    Sentry hands us the event to edit before transmission. The default scrubber
    only drops denylisted dict keys, so a token embedded in a URL string survives.
    """

    # before_send's contract is in-place edits; the client sends this same object
    _scrub(event, set())
    return event


def redact_exception_chain(exc: BaseException) -> None:
    "rewrite exception messages so `str(exc)` no longer contains the access token"

    seen: set[int] = set()

    def walk(current: BaseException | None) -> None:
        if current is None or id(current) in seen:
            return

        seen.add(id(current))
        _redact_exception(current)

        for arg in current.args:
            if isinstance(arg, BaseException):
                walk(arg)

        walk(current.__cause__)
        walk(current.__context__)

    walk(exc)


def _redact_exception(exc: BaseException) -> None:
    if exc.args:
        exc.args = tuple(
            scrub_access_token(arg) if isinstance(arg, str) else arg for arg in exc.args
        )

    # urllib3 keeps the URL on the instance, separate from the message baked into args
    _redact_string_attr(exc, "url")
    _redact_string_attr(exc, "_message")

    request = exc.__dict__.get("request")
    if request is not None:
        _redact_string_attr(request, "url")


def _redact_string_attr(obj: object, name: str) -> None:
    attributes = getattr(obj, "__dict__", None)
    if not isinstance(attributes, dict) or name not in attributes:
        return

    current = attributes[name]
    if isinstance(current, str):
        attributes[name] = scrub_access_token(current)


def _scrub(value: object, seen: set[int]) -> object:
    if isinstance(value, str):
        return scrub_access_token(value)

    if isinstance(value, dict):
        if id(value) in seen:
            return value

        seen.add(id(value))

        for key, item in value.items():
            if isinstance(key, str) and key.lower() in _SECRET_DICT_KEYS:
                value[key] = FILTERED_SECRET
                continue

            value[key] = _scrub(item, seen)

        return value

    if isinstance(value, list):
        if id(value) in seen:
            return value

        seen.add(id(value))

        for index, item in enumerate(value):
            value[index] = _scrub(item, seen)

        return value

    if isinstance(value, tuple):
        return tuple(_scrub(item, seen) for item in value)

    return value
