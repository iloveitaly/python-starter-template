from decouple import config

from .environments import is_production, is_staging

NO_COLOR = config("NO_COLOR", cast=bool, default=False)
"supports NO_COLOR standard: https://no-color.org/"


# BUILD_COMMIT is autogenerated for you if you use the build scripts in this template
# you'll need to set it manually if you're not using the build scripts
if is_production() or is_staging():
    BUILD_COMMIT = config("BUILD_COMMIT", cast=str)
else:
    BUILD_COMMIT = "dev"
