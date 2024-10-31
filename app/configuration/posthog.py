from decouple import config
from posthog import Posthog

from app.environments import is_production

posthog = Posthog(config("POSTHOG_SECRET_KEY"), host=config("POSTHOG_HOST"))

if not is_production():
    posthog.disabled = True
