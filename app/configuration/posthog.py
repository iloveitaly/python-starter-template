import posthog

from app.env import env
from app.environments import is_production


# TODO we should have an automated test for this, probably using an integration test, where posthog is NOT disabled
def posthog_error_handler(error, batch):
    from app import log

    log.warning("posthog error", error=error, batch=batch)


posthog_client = posthog.Posthog(
    project_api_key=env.str("POSTHOG_SECRET_KEY"),
    host=env.str("POSTHOG_HOST", "https://us.i.posthog.com"),
    # don't use Sentry *and* posthog for error tracking!
    enable_exception_autocapture=False,
    # there is no builtin fastapi integration for exceptions!
    on_error=posthog_error_handler,
)

if not is_production():
    posthog_client.disabled = True

# https://github.com/PostHog/posthog-python/issues/353
# without this, a newly-created client will be used for things like catching context exceptions
posthog.default_client = posthog_client


def configure_posthog():
    pass


# TODO tie into python debug logic
# posthog.debug = True

# A/B test
# variant = posthog.get_feature_flag("experiment-feature-flag-key", "user_distinct_id")
# TODO implement local evaluation https://posthog.com/docs/feature-flags/local-evaluation
