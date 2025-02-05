"""
RQ may be the right fit for your project, so I've left this configuration in place although it is not in use.

Take a look at the the readme for more information:
"""

from rq import Queue, Retry, Worker

from app.configuration.redis import get_redis

RQ_RETRY = Retry(max=10, interval=[10, 30, 60])
"""
This aggravates me, but it looks like there is no good documentation on how to implement
more advanced retries:

- https://github.com/mikemill/rq_retry_scheduler
- https://discord.com/channels/844816706231861248/844816707126296578/1330917074406473840

The currently-implemented retry strategy is not great, but we can adjust later
since we've implemented the job logic in a pretty queue-agnostic way.
"""

q = Queue(connection=get_redis())

# must use spawn worker: https://github.com/rq/rq/issues/2058

# TODO do we need to do anything fancy for database connections?

# if __name__ == "__main__":
#     worker = Worker(map(Queue, listen))
#     worker.work()
