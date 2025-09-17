# NOTE common configuration for testing and development
#
#   - Some configuration here is testing specific, but changing *all* environment variables
#     to test mode is a pain, so we include them here to easily run pytest and friends locally.
#   - Do NOT include quotes in any of the values here. This will cause downstream issues when building containers.
#     Docker does not like quotes in any of it's env files or vars.

# required when running pytest, python, etc; not required when running fastapi and ipython
# PYTHONSAFEPATH=1 prevents PWD from being added to sys.path automatically
export PYTHONPATH=.

# use a non-standard port to avoid conflicts with other applications
export PYTHON_SERVER_PORT=8200
export PYTHON_TEST_SERVER_PORT=8201
export PYTHON_TEST_SERVER_HOST=api-test.web.localhost

# job monitoring configuration
export FLOWER_PASSWORD=password
export FLOWER_PORT=8205

# output directory is used by CI and justfiles
export TMP_DIRECTORY=tmp
export TEST_RESULTS_DIRECTORY=$TMP_DIRECTORY/test-results
export PLAYWRIGHT_RESULT_DIRECTORY=$TEST_RESULTS_DIRECTORY/playwright
export PLAYWRIGHT_VISUAL_SNAPSHOT_DIRECTORY=tests/integration/__snapshots__
# without this, playwright will use a different browser path across linux and macos
export PLAYWRIGHT_BROWSERS_PATH=~/.cache/ms-playwright

# used for py tests, justfile recipes, and JS build
# use an absolute path since this is run from within `web/`
export OPENAPI_JSON_PATH=$PWD/web/openapi.json

# only applicable in development, javascript is bundled in the py container in prod
export JAVASCRIPT_SERVER_PORT=8202
export JAVASCRIPT_SERVER_HOST=web.localhost

export PYTHON_SERVER_HOST=api.web.localhost

# TODO we could just choose to have the frontend logic add the protocol?
# protocol is important, otherwise you'll get CORS errors in browser
export VITE_PYTHON_URL="https://${PYTHON_SERVER_HOST}/"
export VITE_APP_BASE_URL="https://${JAVASCRIPT_SERVER_HOST}"

# default from address for the mailer system
export EMAIL_FROM_ADDRESS="noreply@example.com"

# set these conditionally so they be overwritten by CI (or `.env.local`), which has a different server configuration
if [ -z "${DATABASE_HOST:-}" ] && [ -z "${REDIS_HOST:-}" ] && [ -z "${SMTP_HOST:-}" ]; then
  # .orb.local is a nice-to-have feature from: https://docs.orbstack.dev/docker/domains
  # you can replace with localhost or any other postgres/redis host
  SERVICES_HOST=$(basename $PWD).orb.local
  REDIS_HOST=redis.${SERVICES_HOST}
  DATABASE_HOST=postgres.${SERVICES_HOST}
  SMTP_HOST=mailpit.${SERVICES_HOST}
fi

# names are important here: pg_isready and docker configuration requires these
# if you are not using docker for local postgres and redis, you can change these
export POSTGRES_USER=root
export POSTGRES_PASSWORD=password
export POSTGRES_DB=development

export REDIS_URL=redis://${REDIS_HOST}:6379/1
export DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${DATABASE_HOST}:5432/development
export SMTP_URL=smtp://${SMTP_HOST}:1025

#######################
# Secrets
#######################

# NOTE OP_ACCOUNT and OP_VAULT_UID are *not* required when using a service account to access, which is what is used
#      on CI. This is because `OP_SERVICE_ACCOUNT_TOKEN` is tied to a single vault.

# specify the 1p account that should be used to source secrets via `op read`
# export OP_ACCOUNT=yourdomain.1password.com

#
# right click on the vault with your secrets and copy the UID
export OP_VAULT_UID=g46wit25zdsr2ul7yivj4air2u

# random secret key for fastapi session signing
export SESSION_SECRET_KEY=de76c21e-e79d-4ad8-8e89-80ec58c71997

# block bad hosts in fastapi. not required for development, but helpful to keep prod vs dev consistent
# in production, this is most likely only a single host but can support multiple hosts
export ALLOWED_HOST_LIST="$JAVASCRIPT_SERVER_HOST,$PYTHON_TEST_SERVER_HOST,api.web.localhost"

# Some notes on 1Password usage here:
#
# - 1P references with names can change over time and introduce mutation risk, which is why we use the UIDs instead
# - `inject` is much faster than individually sourcing keys with `op read`, which is why we have this wonky heredoc format
# - Env var values should be in the format of "op://${OP_VAULT_UID}/epctgojloj7legp7h62zktshha/sandbox-clerk-secret-key"

op_inject_source <<'EOF'
export CLERK_PRIVATE_KEY="op://${OP_VAULT_UID}/epctgojloj7legp7h62zktshha/sandbox-clerk-secret-key"
export OPENAI_API_KEY="op://${OP_VAULT_UID}/3kilfl4b5gegds7anifvali6zu/credential"
export SENTRY_DSN="op://${OP_VAULT_UID}/4dsjcmjzybuipafki2wl2eovsy/backend-dsn"
export POSTHOG_SECRET_KEY="fake"

export VITE_SENTRY_DSN="op://${OP_VAULT_UID}/4dsjcmjzybuipafki2wl2eovsy/frontend-dsn"
export VITE_CLERK_PUBLIC_KEY="op://${OP_VAULT_UID}/epctgojloj7legp7h62zktshha/sandbox-clerk-public-key"
export VITE_POSTHOG_KEY="op://${OP_VAULT_UID}/25dj3ith4d37cy5ghssr3mo5rq/public-key"
export VITE_POSTHOG_HOST="op://${OP_VAULT_UID}/25dj3ith4d37cy5ghssr3mo5rq/posthog-host"
EOF

export CLERK_PUBLISHABLE_KEY=$VITE_CLERK_PUBLIC_KEY
