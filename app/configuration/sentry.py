import sentry_sdk
import sentry_sdk.integrations
from sentry_sdk.transport import Transport

from app.constants import BUILD_COMMIT
from app.env import env

from ..environments import is_job_monitor, is_production, python_environment

# Outside production: valid DSN shape so the client activates, paired with
# SinkholeTransport (never used for network I/O).
SENTRY_DSN = (
    env.str("SENTRY_DSN")
    if is_production()
    else "https://public@localhost/1"
)


class SinkholeTransport(Transport):
    """
    Drop all Sentry envelopes instead of sending them.

    We ran into a production-only failure because Sentry was not initialized outside
    production (integrations never patched FastAPI/Starlette locally). Matching prod
    configuration here and sinkholing events keeps instrumentation parity without
    sending data to Sentry.io.

    Official guidance for swapping the transport (e.g. unit-testing / special deploys):
    https://docs.sentry.io/platforms/python/configuration/options/#transport
    """

    def capture_envelope(self, envelope) -> None:
        from app import log

        item_types = [item.type for item in envelope.items]
        log.warning(
            "sentry event sinkholed (not sent)",
            item_types=item_types,
        )


def configure_sentry(integrations=None):
    """
    - Sentry used to support posthog, but it doesn't anymore: https://github.com/PostHog/posthog-python/pull/262
    - Non-production uses a fake DSN + SinkholeTransport so integrations still load
      without sending events (see SinkholeTransport docstring).
    """

    if integrations is None:
        integrations = []

    from app import log

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

    sinkhole = not is_production()

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        # None uses the SDK default HTTP transport
        transport=SinkholeTransport() if sinkhole else None,
        release=BUILD_COMMIT,
        environment=python_environment(),
        enable_tracing=True,
        traces_sample_rate=0.1,
        # posthog integration is not a standard integration included with Sentry
        # https://docs.sentry.io/platforms/python/integrations/
        integrations=integrations,
        # these have a way of piling up quickly if they aren't ignored!
        ignore_errors=["WebhookDeliveryError"],
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
        sinkhole=sinkhole,
    )
