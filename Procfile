# Whether or not you use a Procfile in production, it's a great a way to canonically define your process types.
# Since this is effectively a simple yaml file, you can extract process types using yq or other tooling rather than
# scattering and duplicating process definitions throughout your codebase.

api: python main.py
# in a more complex application, you'll want to run a separate scheduler instead of running the scheduler inline
worker: celery -A app.jobs worker --beat
scheduler: celery -A app.jobs beat
job_monitor: celery -A app.celery flower --basic-auth=:$FLOWER_PASSWORD --port=$FLOWER_PORT
console: bash -l
