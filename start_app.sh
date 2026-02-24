#!/bin/zsh
# Get dynamic ports from Docker
POSTGRES_PORT=$(docker port python-template-postgres-1 5432 | cut -d: -f2)
REDIS_PORT=$(docker port python-template-redis-1 6379 | cut -d: -f2)

# Run with auto-detected ports
ALLOWED_HOST_LIST="*" \
OPENAI_API_KEY=api-key \
CLERK_PRIVATE_KEY=sk_test \
POSTHOG_SECRET_KEY=secret \
DATABASE_URL=postgresql://root:password@127.0.0.1:$POSTGRES_PORT/development \
REDIS_URL=redis://127.0.0.1:$REDIS_PORT/1 \
uv run fastapi dev app/server.py --app api_app --host 0.0.0.0 --port 8200
