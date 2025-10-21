"""Pytest plugin for Celery testing utilities."""

from functools import reduce
from operator import getitem
from typing import Any, Callable, Union

import kombu.utils.json
import pytest
import redis


# TODO use funcy version once it is released
def dig(path, data, *, default=None):
    """
    Dig into nested dict using dot-path string or list of keys.
    Raises KeyError/TypeError if path missing and no default.

    >>> dig('a.b', {'a': {'b': 1}})
    1
    >>> dig('a.b', {'a': {'b': 1}}, default=42)
    1
    >>> dig('a.x', {'a': {'b': 1}}, default=42)
    42
    >>> dig('a.x', {'a': {'b': 1}})
    Traceback (most recent call last):
    ...
    KeyError: 'x'
    >>> dig(['a', 'b'], {'a': {'b': 1}})
    1
    """
    keys = path.split(".") if isinstance(path, str) else path
    try:
        return reduce(getitem, keys, data)
    except (KeyError, TypeError) as e:
        if default is not None:
            return default
        raise e


class CeleryTestUtils:
    """
    Collection of utilities for testing Celery tasks, assuming no worker is running.

    This is not designed to be performant, but it's useful for testing.
    """

    def __init__(self, celery_app: Any) -> None:
        self.celery_app = celery_app
        if not self.celery_app.conf.broker_url.startswith("redis"):
            raise ValueError("Only Redis broker supported")
        self.queues = list(self.celery_app.amqp.queues.keys()) or ["celery"]
        self.redis_client = redis.from_url(self.celery_app.conf.broker_url)

    def get_all_queued_tasks(self) -> list[dict[str, Any]]:
        """
        Example response element:

        {
            'body': 'W1t7Il9fdHlwZV9fIjogInR5cGVpZC50eXBlaWQuVHlwZUlEIiwgIl9fdmFsdWVfXyI6ICJ3aF8wMWs3bXk5MjA5ZXpwOWY5bmpjdGtzMmcxdiJ9XSwge30sIHsiY2FsbGJhY2tzIjogbnVsbCwgImVycmJhY2tzIjogbnVsbCwgImNoYWluIjogbnVsbCwgImNob3JkIjogbnVsbH1d',
            'content-encoding': 'utf-8',
            'content-type': 'application/json',
            'headers': {
                'lang': 'py',
                'task': 'app.jobs.process_webhook.perform',
                'id': '1e2a793c-914b-4518-8fe5-005a2e319c19',
                'shadow': None,
                'eta': None,
                'expires': None,
                'group': None,
                'group_index': None,
                'retries': 0,
                'timelimit': [None, None],
                'root_id': '1e2a793c-914b-4518-8fe5-005a2e319c19',
                'parent_id': None,
                'argsrepr': "(TypeID('wh_01k7my9209ezp9f9njctks2g1v'),)",
                'kwargsrepr': '{}',
                'origin': 'gen55253@BiancoBook',
                'ignore_result': False,
                'replaced_task_nesting': 0,
                'stamped_headers': None,
                'stamps': {}
            },
            'properties': {
                'correlation_id': '1e2a793c-914b-4518-8fe5-005a2e319c19',
                'reply_to': '492ecc7c-8751-3139-9ad0-0864695bf756',
                'delivery_mode': 2,
                'delivery_info': {'exchange': '', 'routing_key': 'celery'},
                'priority': 0,
                'body_encoding': 'base64',
                'delivery_tag': '293f71c0-8047-4ac0-8945-fe7f7df1d42f'
            }
        }
        """

        all_tasks = []
        for queue in self.queues:
            raw_queue_contents = self.redis_client.lrange(queue, 0, -1)

            if not raw_queue_contents:
                continue

            # kombu types are terrible :/
            queue_contents = [kombu.utils.json.loads(msg) for msg in raw_queue_contents]  # type: ignore
            all_tasks.extend(queue_contents)

        return all_tasks

    def jobs_of_type(self, task: Union[str, Callable]) -> list[dict[str, Any]]:
        task_name = task.name if callable(task) else task  # type: ignore
        all_tasks = self.get_all_queued_tasks()
        return [
            t for t in all_tasks if dig("headers.task", t, default=None) == task_name
        ]

    def count_jobs_of_type(self, task: Union[str, Callable]) -> int:
        return len(self.jobs_of_type(task))


@pytest.fixture
def celery_utils(celery_app: Any) -> CeleryTestUtils:
    return CeleryTestUtils(celery_app)
