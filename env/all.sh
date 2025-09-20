# NOTE: configuration which should be used across all environments (including production!) should go here

# standard python config
export PYTHONFAULTHANDLER=1
export PYTHONUNBUFFERED=1
export PYTHONHASHSEED=random
export PYTHONDONTWRITEBYTECODE=1
# Don't automatically add PWD to PYTHONPATH
export PYTHONSAFEPATH=1
# Make Python use UTF-8 encoding for output to stdin, stdout, and stderr.
export PYTHONIOENCODING='UTF-8'
export TZ=UTC
