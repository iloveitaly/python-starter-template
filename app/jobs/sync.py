from app import log
from app.celery import celery_app


@celery_app.task()
def perform():
    log.info("can run multiple instances with the same argument")
    return True
