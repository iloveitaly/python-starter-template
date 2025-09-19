from decouple import config
from posthog import Posthog

from app.environments import is_production

posthog_client = Posthog(
    config("POSTHOG_SECRET_KEY"),
    host=config("POSTHOG_HOST", default="https://us.i.posthog.com"),
)

if not is_production():
    posthog_client.disabled = True


def configure_posthog():
    pass


# TODO tie into python debug logic
# posthog.debug = True

# A/B test
# variant = posthog.get_feature_flag("experiment-feature-flag-key", "user_distinct_id")
# TODO implement local evaluation https://posthog.com/docs/feature-flags/local-evaluation
