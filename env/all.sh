# NOTE: configuration which should be used across all environments (including production!) should go here

# standard python config
export PYTHONFAULTHANDLER=1
# never buffer output streams
export PYTHONUNBUFFERED=1
# ensures dict order is not relied upon
export PYTHONHASHSEED=random
# https://www.erdaltaskesen.com/blog/how-to-remove-pycache-folders-and-pyc-files/
# https://github.com/pytest-dev/pytest/issues/200
export PYTHONDONTWRITEBYTECODE=1
# Don't automatically add PWD to PYTHONPATH
export PYTHONSAFEPATH=1
# Make Python use UTF-8 encoding for output to stdin, stdout, and stderr.
export PYTHONIOENCODING='UTF-8'
# without this, the timezone will change depending on the container/environment
export TZ=UTC
