from decouple import config

NO_COLOR = config("NO_COLOR", cast=bool, default=False)
"supports NO_COLOR standard: https://no-color.org/"
