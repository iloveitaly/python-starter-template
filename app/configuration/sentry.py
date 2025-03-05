import sentry_sdk
import sentry_sdk.integrations
from decouple import config
from posthog.sentry.posthog_integration import PostHogIntegration

from ..environments import is_job_monitor, is_production, python_environment


def configure_sentry(integrations=[]):
    from app import log

    if not is_production():
        return

    if is_job_monitor():
        # we don't care about monitoring the job monitoring frontend
        return

    def filter_transactions(event, _hint):
        """
        Filter out noisy urls that don't add any value to profiling

        - https://docs.sentry.io/platforms/python/configuration/filtering/
        - https://github.com/getsentry/sentry-docs/pull/6364/files
        """
        from urllib.parse import urlparse

        IGNORED_PATHS = ["/healthcheck", "/", "{path:path}"]

        url_string = event["request"]["url"]
        parsed_url = urlparse(url_string)

        if parsed_url.path in IGNORED_PATHS or parsed_url.path.startswith("/assets/"):
            return None

        return event

    sentry_sdk.init(
        dsn=config("SENTRY_DSN", cast=str),
        release=config("BUILD_COMMIT", cast=str),
        environment=python_environment(),
        enable_tracing=True,
        traces_sample_rate=0.1,
        # posthog integration is not a standard integration included with Sentry
        # https://docs.sentry.io/platforms/python/integrations/
        integrations=[PostHogIntegration()] + integrations,
        before_send_transaction=filter_transactions,
        _experiments={
            # Set continuous_profiling_auto_start to True
            # to automatically start the profiler on when
            # possible.
            "continuous_profiling_auto_start": True,
        },
    )

    log.info(
        "sentry configured",
        integrations=sentry_sdk.integrations._installed_integrations,
    )
