import posthog
from decouple import config

from app.environments import is_production

posthog_client = posthog.Posthog(
    project_api_key=config("POSTHOG_SECRET_KEY"),
    host=config("POSTHOG_HOST", default="https://us.i.posthog.com"),
    # don't use Sentry *and* posthog for error tracking!
    enable_exception_autocapture=False,
    # there is no builtin fastapi integration for exceptions!
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
