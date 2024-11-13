from decouple import config

CLERK_PRIVATE_KEY = config("CLERK_PRIVATE_KEY", cast=str)
