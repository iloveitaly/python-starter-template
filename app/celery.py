from datetime import timedelta

import celery_healthcheck
from celery import Celery, signals
from celery.app.task import Task
from celery.schedules import crontab

from app import log, root
from app.configuration.redis import redis_url

from activemodel.celery import register_celery_typeid_encoder

# https://github.com/sbdchd/celery-types
Task.__class_getitem__ = classmethod(lambda cls, *args, **kwargs: cls)  # type: ignore[attr-defined]

register_celery_typeid_encoder()


class BaseTaskWithRetry(Task):
    """
    Base task class with extended retry capabilities. The default retry sequence is very fast, we use a longer
    retry sequence in case an external system is down.

    This class extends the Celery Task class to implement a slower retry sequence,
    which is useful when dealing with external systems (like openai) that might be temporarily down
    or rate limited.

    Attributes:
        autoretry_for (tuple): Exceptions that trigger automatic retry. Default is (Exception,),
                              which means any exception will trigger a retry.
        max_retries (int): Maximum number of retry attempts. Default is 20.
        retry_backoff (bool): Whether to use exponential backoff. Default is True.
        retry_backoff_max (int): Maximum backoff time in seconds. Default is 700.
        retry_jitter (bool): Whether to add random jitter to backoff. Default is True.
    """

    autoretry_for = (Exception,)
    max_retries = 20
    retry_backoff = True
    retry_backoff_max = 700
    retry_jitter = True

    # TODO should probably add a CM for the database session here...


celery_app = Celery(
    "tasks",
    broker=redis_url(),
    # TODO why is this causing typing issues?
    # result_backend=redis_url(),
)

# endpoint for running a TCP healthcheck on the container
celery_healthcheck.register(celery_app)

# define a hard timeout to limit infinitely running processes
# 35m is an arbitrary number, but should be long enough to handle most tasks
celery_app.conf.task_time_limit = 60 * 35

# keep results around for 30d, otherwise they are pulled from the flower UI and it's hard to see what happened
celery_app.conf.result_expires = 60 * 60 * 24 * 30

# By default, is a worker is killed without warning (OOM, etc) which can occur more easily in containerized environments
# the job will get into a stale state where it looks like it is executing indefinitely and will never be retried.
# in order to ensure that the job is retried if the process is killed abruptly, we need to enable two settings:
#
#   - acks_late: "The acks_late setting would be used when you need the task to be executed again if the worker (for some reason) crashes mid-execution"
#   - task_reject_on_worker_lost: job is not retried if the worker is lost
#
# References:
#
#   - https://stackoverflow.com/questions/45045980/what-different-between-task-reject-on-worker-lost-and-task-acks-late-in-celery
#   - https://stackoverflow.com/questions/69107860/celery-what-is-the-reason-to-have-acks-late-true-without-setting-task-reject-on
celery_app.conf.task_reject_on_worker_lost = True
celery_app.conf.task_acks_late = True

celery_app.conf.beat_schedule_filename = str(root / "tmp/celerybeat-schedule")


@signals.celeryd_init.connect
def init_sentry(**_kwargs):
    # according to sentry documentation, this must be done here, even if it's executed on application start
    # https://docs.sentry.io/platforms/python/integrations/celery/
    from sentry_sdk.integrations.celery import CeleryIntegration

    configure_sentry(integrations=[CeleryIntegration(monitor_beat_tasks=True)])


@signals.setup_logging.connect
def receiver_setup_logging(
    loglevel, logfile, format, colorize, **kwargs
):  # pragma: no cover
    # this ensures celery does not override our application's logging configuration
    pass


@signals.worker_init.connect
def worker_init_import_jobs(sender, **kwargs):
    import app.jobs  # noqa: F401
    # ensures all job classes are available to celery and avoids circular imports
    # that would be caused by adding them as a top-level import


@signals.worker_process_init.connect
def worker_process_init_setup_logging(**kwargs):
    # TODO should add PID and worker ID to the log content, we want the `WARNING/ForkPoolWorker-8` ID in the logs
    #      https://github.com/celery/celery/discussions/9378
    # might need to grab this from? https://pypi.org/project/setproctitle/#history
    # log.local(celery_pid=sender.pid)
    pass


# tag all jobs with the job name (module path) and uuid for the task
@signals.task_prerun.connect
def on_task_prerun(sender, task_id, task, args, kwargs, **_kwargs):
    "https://github.com/hynek/structlog/issues/287#issuecomment-991182054"
    log.clear()
    log.local(task_id=task_id, task_name=task.name)


# TODO below should be cleaned up and is probably overkill, need to determine exactly which one we should use
@signals.task_postrun.connect
def on_task_postrun(sender, task_id, task, args, kwargs, retval, state, **_kwargs):
    log.clear()


@signals.worker_shutdown.connect
def capture_worker_stop(sender, **kwargs):
    log.clear()


# celery.conf.app_name = "tasks"
# celery.conf.log_level = "INFO"

# https://stackoverflow.com/questions/26831103/avoiding-duplicate-tasks-in-celery-broker
celery_app.conf.ONCE = {
    "backend": "celery_once.backends.Redis",
    "settings": {"url": redis_url(), "default_timeout": 60 * 60},
}

celery_app.conf.beat_schedule = {
    "example_normal": {
        "task": "app.jobs.example_normal",
        # can run sub-minute schedules
        "schedule": timedelta(seconds=2),
    },
    "sync_clerk": {
        "task": "app.jobs.sync_clerk.perform",
        "schedule": crontab(minute="0", hour="0"),
    },
}

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
