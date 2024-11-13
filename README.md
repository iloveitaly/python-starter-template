# Python & React Router Project Template

This is an extremely opinionated template for a Python and React project. Here's the stack:

* Python + FastAPI + SQLModel + SQLAlchemy + Alembic + Celery
* TypeScript + React + Vite + React Router (in SPA mode) + ShadCN + Tailwind + ESLint + Prettier
* Postgres + Redis
* Sentry + Clerk + PostHog
* Docker (via nixpacks) for containerization
* GitHub Actions for CI/CD
* Direnv + 1Password for secret management

## Cost of Complexity

There are many things I don't like about this setup. There's a cost to going this router and I'm not sure if it's worth it.

It's all about tradeoffs:

1. Use rails and hotwire. You lose React and all of the amazing ui libraries that come with it. You make hiring harder. You lose typing.
2. Use full stack javascript. You have to work with Javascript everyday.
3. Use this approach. You lose the beauty of batteries-included-rails and the deployment simplicity of the other approaches.

### Architecture Notes

notes:
assume injection of pretty traceback
ipython in prod for console exploration
typing from python to typescript via pyright + openapi + typescript library gen
react-router seems to wrap `vite preview`
direnv allow config

## Deployment

* Containers should be used instead of proprietary build systems (Heroku, etc).
* Ability to build production-identical containers locally for debugging
* Container building should be handled on CI

## Other Project Templates

* https://github.com/peterdresslar/fastapi-sqlmodel-alembic-pg
* https://github.com/fastapi/full-stack-fastapi-template/
* https://github.com/epicweb-dev/epic-stack/blob/main/docs/examples.md
* https://github.com/tierrun/tier-vercel-openai
* https://github.com/shadcn-ui/next-template

## Great Open Source Projects

* https://github.com/danswer-ai/danswer
* https://github.com/developaul/translate-app
* https://github.com/vercel/ai-chatbot