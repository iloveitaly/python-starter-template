from decouple import config
from posthog import Posthog

from app.environments import is_production

posthog = Posthog(config("POSTHOG_SECRET_KEY"), host=config("POSTHOG_HOST"))

# TODO tie into python debug logic
# posthog.debug = True

# A/B test
# variant = posthog.get_feature_flag("experiment-feature-flag-key", "user_distinct_id")

# TODO implement local evaluation https://posthog.com/docs/feature-flags/local-evaluation

if not is_production():
    posthog.disabled = True
