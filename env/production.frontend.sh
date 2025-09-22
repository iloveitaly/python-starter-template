# NOTE This line is very important! This turns off dev dependencies *within* the docker build it's unclear if this
#      is the optimal approach. The logic here is the build process *is* the production environment since it's a SPA
#      so we want to simulate that environment the best we can.
export NODE_ENV=production

export VITE_PYTHON_URL="/"

# used for generating absolute urls on the frontend
export VITE_APP_BASE_URL=https://example.com/

# one of the few duplicated env variables, required for the openapi build
export OPENAPI_JSON_PATH=openapi.json

# `inject` is much faster than individually sourcing keys with `op read`
# IMPORTANT: these should only be used in production!
op_inject_source <<'EOF'
export VITE_SENTRY_DSN="op://${OP_VAULT_UID}/4dsjcmjzybuipafki2wl2eovsy/frontend-dsn"
export VITE_CLERK_PUBLIC_KEY="op://${OP_VAULT_UID}/epctgojloj7legp7h62zktshha/sandbox-clerk-public-key"
export VITE_POSTHOG_KEY="op://${OP_VAULT_UID}/25dj3ith4d37cy5ghssr3mo5rq/public-key"
export VITE_POSTHOG_HOST="op://${OP_VAULT_UID}/25dj3ith4d37cy5ghssr3mo5rq/posthog-host"

# required for vite sentry build. These will be bundled into the container, but this container is never pushed publicly.

# created a new organization token at: /settings/auth-tokens/
export SENTRY_AUTH_TOKEN="op://${OP_VAULT_UID}/4dsjcmjzybuipafki2wl2eovsy/authorization-token"
# slug is located at: /settings/organization/
export SENTRY_ORG="op://${OP_VAULT_UID}/4dsjcmjzybuipafki2wl2eovsy/organization-slug"
export SENTRY_PROJECT="op://${OP_VAULT_UID}/4dsjcmjzybuipafki2wl2eovsy/frontend-project"
EOF
