import sentry_sdk
from decouple import config

from ..environments import is_production


def configure_sentry():
    if not is_production():
        return

    # TODO does this still need happen?
    # TODO https://github.com/getsentry/sentry-docs/pull/6364/files
    def filter_transactions(event, _hint):
        from urllib.parse import urlparse  # pylint: disable=import-outside-toplevel

        url_string = event["request"]["url"]
        parsed_url = urlparse(url_string)

        if parsed_url.path == "/healthcheck":
            return None

        return event

    sentry_sdk.init(
        dsn=config("SENTRY_DSN", cast=str),
        enable_tracing=True,
        traces_sample_rate=0.1,
        integrations=[
            # FlaskIntegration(),
        ],
        before_send_transaction=filter_transactions,
    )
