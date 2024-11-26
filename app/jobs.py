import asyncio
from datetime import timedelta

from celery import Celery
from celery.schedules import crontab
from celery_once import QueueOnce

from app import log
from app.configuration.redis import redis_url

celery = Celery(
    "tasks",
    broker=redis_url(),
    result_backend=redis_url(),
)

# celery.conf.app_name = "tasks"
# celery.conf.log_level = "INFO"

# https://stackoverflow.com/questions/26831103/avoiding-duplicate-tasks-in-celery-broker
celery.conf.ONCE = {
    "backend": "celery_once.backends.Redis",
    "settings": {"url": redis_url(), "default_timeout": 60 * 60},
}

celery.conf.beat_schedule = {
    "example_normal": {
        "task": "app.jobs.example_normal",
        # can run sub-minute schedules
        "schedule": timedelta(seconds=2),
    },
    "example_exactly_once": {
        "task": "app.jobs.example_exactly_once",
        "schedule": crontab(minute="*/60"),
    },
    "example_async": {
        "task": "app.jobs.example_async",
        "schedule": crontab(minute="*/5"),
    },
}

# define a hard timeout to limit infinitely running processes
celery.conf.task_time_limit = 60 * 35


# from app.configuration.database import clear_engine
# @task_prerun.connect
# def on_task_init(*args, **kwargs):
#     """
#     Without this, the database connection becomes corrupted and causes SSL-related failures:

#     https://github.com/celery/celery/issues/1564
#     https://github.com/celery/celery/issues/3238
#     https://stackoverflow.com/questions/45215596/flask-and-celery-on-heroku-sqlalchemy-exc-databaseerror-psycopg2-databaseerro
#     """

#     log.info("task init, clearing database engine")

#     clear_engine()


@celery.task()
def example_normal():
    log.info("can run multiple instances with the same argument")


@celery.task(base=QueueOnce)
def example_exactly_once(menu_id: int):
    log.info("will only run one at a time")


@celery.task()
def example_async():
    async def _example_async():
        log.info("generating events")

    asyncio.run(_example_async())
