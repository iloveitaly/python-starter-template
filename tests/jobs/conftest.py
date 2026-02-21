import pytest
from celery import Celery

from app.celery import celery_app


@pytest.fixture
def default_worker_app(default_worker_app: Celery) -> Celery:
    return celery_app
