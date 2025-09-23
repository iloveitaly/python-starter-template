---
mode: 'agent'
description: ''
---
## Secrets

Here's how environment variables are managed in this application:

- `.envrc` entry point to load the correct env stack. Should not contain secrets and should be simple some shell logic and direnv stdlib calls.
- `.env` common configuration for all systems. No secrets. No dotenv/custom scripts. Just `export`s to modify core configuration settings like `export TZ=UTC`.
- `.env.local` overrides across all environments (dev and test). Useful for things like 1Password service account token and database hosts which mutate the logic followed in `.env.shared`. Not committed to source control.
- `.env.shared` This contains the bulk of your system configuration. Shared across test, CI, dev, etc but not production.
- `.env.shared.local` Override `.env.shared` configuration locally. Not committed to source.
- `.env.dev.local` configuration overrides for non-test environments. `PYTHONBREAKPOINT`, `LOG_LEVEL`, etc. Most of your environment changes end up happening here.
- `.env.test` test-only environment variables (`PYTHON_ENV=test`). This file should generally be short.
- `.env.production.{backend,frontend}` for most medium-sized projects you'll have separate frontend and backend systems (even if your frontend is SPA, which I'm a fan of). These two files enable you to document the variables required to build (in the case of a SPA frontend) or run (in the case of a python backend) your system in production.
- `*.local` files have a `-example` variant which is committed to version control. These document helpful environment variables for local development.
- When writing TypeScript/JavaScript/React, use `requireEnv("THE_ENV_VAR_NAME")` to read an environment variable. `import {requireEnv} from '~/utils/environment'`
