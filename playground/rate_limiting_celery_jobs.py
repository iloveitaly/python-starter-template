import random
from celery.exceptions import Reject
from limits import RateLimitItemPerSecond, storage, strategies
from app.configuration.redis import redis_url

# TODO this is broken and does not work :/
# TODO should pull into base class, we are just adding the rate limit retry stuff
class CustomTask(BaseTaskWithRetry):
    def retry(
        self,
        args=None,
        kwargs=None,
        exc=None,
        throw=True,
        eta=None,
        countdown=None,
        max_retries=None,
        **options,
    ):
        # If it's a rate limit exception, don't count it against retries
        if isinstance(exc, RateLimitExceeded):
            # Schedule a new task instead of using the retry mechanism
            # This bypasses the retry counter entirely
            jitter = random.uniform(0, 60 * 10)
            delay = 10 + jitter  # Base delay of 10 seconds plus jitter

            log.info(
                "rate limit hit, scheduling new task",
                delay=delay,
                task_id=self.request.id,
            )

            # Create a completely new task that doesn't affect retry count
            self.apply_async(
                args=args or self.request.args,
                kwargs=kwargs or self.request.kwargs,
                countdown=delay,
            )

            # Raise Reject to remove current task from queue without marking as failure
            raise Reject("Rate limited", requeue=False)

        # For all other exceptions, use normal retry behavior with backoff
        return super().retry(
            args=args,
            kwargs=kwargs,
            exc=exc,
            throw=throw,
            eta=eta,
            countdown=countdown,
            max_retries=max_retries,
            **options,
        )

# TODO rename to something more generic
class RateLimitExceeded(Exception):
    def __init__(self, message, delay=10):
        super().__init__(message)
        self.delay = delay


class CustomRateLimiter:
    def __init__(self, redis_url):
        # https://help.gohighlevel.com/support/solutions/articles/48001060529-highlevel-api#What-are-the-Rate-Limits-for-API-1.0-&-API-2.0?
        calls_per_request = 3

        self.storage = storage.RedisStorage(
            uri=redis_url,
        )
        self.limiter = strategies.MovingWindowRateLimiter(self.storage)
        self.rates = [
            # 100 per 10s
            RateLimitItemPerSecond(round(100 / calls_per_request), 10),
            # 200k per 24hr
            RateLimitItemPerSecond(round(200000 / calls_per_request), 86400),
        ]

    def hit(self, *identifiers):
        # Test all first
        for rate in self.rates:
            if not self.limiter.test(rate, *identifiers):
                return False

        # Then hit all
        for rate in self.rates:
            self.limiter.hit(rate, *identifiers)

        return True

    # TODO have not tested this
    def reset(self, *identifiers):
        for rate in self.rates:
            key = rate.key_for(*identifiers)
            self.storage.clear(key)


domain_limiter = CustomRateLimiter(redis_url())
