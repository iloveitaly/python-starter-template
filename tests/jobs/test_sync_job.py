from app.jobs.sync import perform


def test_example_normal_task(celery_app, celery_worker):
    result = perform.delay()
    assert result.get(timeout=10) is True
