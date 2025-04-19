from celery_once import QueueOnce

from app import log
from app.celery import celery_app


@celery_app.task(base=QueueOnce)
def perform():
    log.info("will only run one at a time")
