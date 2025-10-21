import httpx
from whenever import Instant

from app import log
from app.celery import BaseTaskWithRetry, celery_app
from app.constants import BUILD_COMMIT

from activemodel.types import TypeIDType

DEFAULT_WEBHOOK_TIMEOUT = 30


@celery_app.task(base=BaseTaskWithRetry)
def perform(event_id: TypeIDType) -> None:
    from app.models.webhook_event import WebhookEvent

    event: WebhookEvent = WebhookEvent.one(event_id)

    # TODO this is problematic as it can flood the queues with rate limit retries since there is not delay when it's put back on the queue
    # TODO we should extract the domain from the distribution
    # if not domain_limiter.hit("gohighlevel"):
    #     # TODO we should end up hitting this limit in some way?
    #     log.info("rate limit exceeded", domain="gohighlevel")
    #     raise RateLimitExceeded("rate limit exceeded")
    #     raise Reject("rate limit exceeded", requeue=True)

    # do not resend if it already succeeded
    if event.succeeded_at is not None:
        log.info(
            "webhook already processed",
            event_id=event.id,
            destination=event.destination,
            # distribution_id=event.distribution_id,
            event_type=event.type,
            skipped=True,
        )
        return

    log.info(
        "POST webhook",
        event_id=event.id,
        destination=event.destination,
        # distribution_id=event.distribution_id,
        event_type=event.type,
        timeout=DEFAULT_WEBHOOK_TIMEOUT,
    )

    try:
        response = httpx.post(
            event.destination,
            json=event.payload,
            headers={
                "Content-Type": "application/json",
                "X-Application-Version": BUILD_COMMIT,
            },
            timeout=DEFAULT_WEBHOOK_TIMEOUT,
        )

        response.raise_for_status()
        event.response_payload = response.json()
    except Exception:
        event.failed_at = Instant.now().py_datetime()
        event.save()
        raise

    # success
    event.failed_at = None
    event.succeeded_at = Instant.now().py_datetime()
    event.save()

    log.info(
        "process webhook end",
        event_id=event.id,
        destination=event.destination,
        # distribution_id=event.distribution_id,
        event_type=event.type,
        status_code=response.status_code,
    )


queue = perform.delay
