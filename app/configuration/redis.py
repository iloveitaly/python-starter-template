import redis
from decouple import config

from ..environments import is_testing


def redis_url():
    if is_testing():
        return config("TEST_REDIS_URL", cast=str)
    else:
        return config("REDIS_URL", cast=str)


REDIS = None


def application_redis_connection():
    global REDIS  # pylint: disable=global-statement

    if REDIS is None:
        # TODO can list specific errors to retry with `retry_on_error`
        # https://github.com/celery/kombu/issues/1018
        REDIS = redis.from_url(redis_url(), retry_on_timeout=True)

    return REDIS
