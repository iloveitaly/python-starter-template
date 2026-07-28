import asyncio

from app import log
from app.celery import celery_app


@celery_app.task()
def perform():
    log.info("starting async job execution")

    async def _example_async():
        log.info("running async job")

    asyncio.run(_example_async())
