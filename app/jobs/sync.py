from typeid import TypeID

from app import log
from app.celery import celery


def perform(object_id: str | TypeID):
    log.info("starting job", object_id=object_id)


# don't use the decorator directly so we can use `perform` directly in a REPL
perform_celery = celery.task(perform)


# TODO there may be some fancy arg parsing we can do here?
#      https://stackoverflow.com/questions/73856901/how-can-i-use-paramspec-with-method-decorators
def queue(*args, **kwargs):
    "always use this method to queue jobs so it's easy to swap out the job system"
    perform_celery.delay(*args, **kwargs)
