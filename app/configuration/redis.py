import redis

from app.env import env

from ..environments import is_testing


def redis_url():
    if is_testing():
        return env.str("TEST_REDIS_URL")
    else:
        return env.str("REDIS_URL")


REDIS = None


def get_redis():
    global REDIS  # pylint: disable=global-statement

    if REDIS is None:
        # TODO can list specific errors to retry with `retry_on_error`
        # https://github.com/celery/kombu/issues/1018
        REDIS = redis.from_url(redis_url(), retry_on_timeout=True)

    return REDIS
