# Updated WSL Ports for Today
export DATABASE_URL=postgresql://root:password@127.0.0.1:49658/development
export REDIS_URL=redis://127.0.0.1:49681/1

# Missing Secrets to fix the crash
export OPENAI_API_KEY=api-key
export CLERK_PRIVATE_KEY=sk_test_placeholder
export POSTHOG_SECRET_KEY=secret-key
export SENTRY_DSN=backend-dsn
export VITE_CLERK_PUBLIC_KEY=pk_test_placeholder
export VITE_POSTHOG_KEY=public-key
export EMAIL_FROM_ADDRESS=keith@mapua.edu.ph
export ALLOWED_HOST_LIST="*"
