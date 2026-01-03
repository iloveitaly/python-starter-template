# Local Development Setup

## Prerequisites

- [mise](https://mise.jdx.dev/) - Tool version manager
- [direnv](https://direnv.net/) - Environment variable manager
- [Docker](https://www.docker.com/) or [OrbStack](https://orbstack.dev/) - For PostgreSQL, Redis, Mailpit
- [just](https://github.com/casey/just) - Command runner

## Quick Start

1. **Clone and enter the repository**
   ```bash
   cd python-starter-template
   ```

2. **Set up local environment variables**
   
   Copy the example files:
   ```bash
   cp env/all.local-example.sh env/all.local.sh
   cp env/dev.local-example.sh env/dev.local.sh
   ```

3. **Configure secrets in `env/all.local.sh`**
   
   Add your API keys (never commit this file - it's gitignored):
   ```bash
   export OPENAI_API_KEY=your-openai-key
   export POSTHOG_SECRET_KEY=your-posthog-key
   export VITE_CLERK_PUBLIC_KEY=your-clerk-public-key
   export CLERK_PUBLISHABLE_KEY=$VITE_CLERK_PUBLIC_KEY
   export CLERK_PRIVATE_KEY=your-clerk-secret-key
   export CLERK_SECRET_KEY=$CLERK_PRIVATE_KEY
   ```

4. **Allow direnv**
   ```bash
   direnv allow
   ```

5. **Run setup**
   ```bash
   just setup
   ```

   This will:
   - Install Python dependencies with `uv`
   - Pull and start Docker containers (postgres, redis, mailpit)
   - Run database migrations
   - Seed the database with test data

## Running the Application

### Backend (FastAPI)
```bash
just dev
```
Runs on `http://localhost:8200`

### Frontend (React Router + Vite)
```bash
cd web && pnpm dev
```
Runs on `http://localhost:8202`

## Database Management

- `just db_migrate` - Run pending migrations
- `just db_reset` - Drop all tables, re-run migrations, and seed
- `just db_seed` - Seed database with test data
- `just db_generate_migration "description"` - Generate a new migration

## Testing

```bash
pytest                              # Run all tests
pytest --ignore=tests/integration   # Skip integration tests
pytest tests/integration            # Run only integration tests
```

## Environment Files

### Tracked in Git
- `env/all.sh` - Global configuration (all environments)
- `env/not_production.sh` - Shared dev/test configuration
- `env/dev.sh` - Development-specific settings
- `env/test.sh` - Test-specific settings
- `env/production.*.sh` - Production configuration

### NOT Tracked in Git (gitignored)
- `env/all.local.sh` - Your personal secrets and overrides
- `env/dev.local.sh` - Your personal dev preferences
- `env/*.local.*` - Any file matching this pattern

## CI/CD Secrets

The following secrets need to be added manually in GitHub repository settings:

1. Go to `https://github.com/YOUR_USERNAME/python-starter-template/settings/secrets/actions`
2. Add these secrets:
   - `CLERK_SECRET_KEY`
   - `CLERK_PRIVATE_KEY`
   - `VITE_CLERK_PUBLIC_KEY`
   - `OPENAI_API_KEY`
   - `POSTHOG_SECRET_KEY`

## Migration Branches

This project uses the Expand & Contract pattern for zero-downtime database migrations:

1. **migration_expand** - Add nullable `service_token` column
2. **migration_dual_write** - Write to both `api_key` and `service_token`
3. **migration_backfill** - Copy existing `api_key` values to `service_token`
4. **migration_contract** - Switch reads to `service_token`, prepare to drop `api_key`

Deploy these branches in order, running the backfill script between phases 2 and 3.
