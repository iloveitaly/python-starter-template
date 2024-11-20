# Python & React Router Project Template

This is an extremely opinionated template for a Python and React project. Here's the stack:

* Justfile + Direnv + Mise + Lefthook + 1Password for local development & secret configuration
* Python + FastAPI + SQLModel + SQLAlchemy + Alembic + Celery
* TypeScript + React + Vite + React Router (in SPA mode) + ShadCN + Tailwind + ESLint + Prettier + HeyAPI (for OpenAPI)
* Postgres + Redis
  * Docker Compose for running locally
  * OrbStack is recommended for local docker development
* Sentry + Clerk + PostHog
* Docker (via nixpacks) for containerization
* GitHub Actions for CI/CD

## Cost of Complexity

There are many things I don't like about this setup. There's a complexity cost to going this route and I'm not sure if it's worth it.

It's all about tradeoffs. For modern web development, there are the options as I see them:

1. Use Rails and HotWire.
   1. You lose React, all of the amazing ui libraries that come with it, the massive JS + Py labor market, great tooling, typing, and finely-tuned LLMs on massive training data.
   2. You get a beautifully crafted battery-included framework.
2. Use full stack javascript.
   1. You have to work with Javascript everyday. I've given up on backend JavaScript. The whole ecosystem is a mess and I don't enjoy working in it. Non-starter for me.
   2. You get access to a massive labor market, great tooling, typing, and finely-tuned LLMs on massive training data.
3. Use React & Python.
   1. You lose simplicity. You have to deal with two languages, which means more complex build systems.
   2. You get full-stack typing (if you do it right).
   3. You can move fast with React and all of the amazing UI libraries built on top of it, without having to deal with full stack JavaScript.
   4. You get access to massive JS + Py labor markets.

#3 is what is implemented here.

## Architecture Notes

notes:
assume injection of pretty traceback
ipython in prod for console exploration
typing from python to typescript via pyright + openapi + typescript library gen
react-router seems to wrap `vite preview`
direnv allow config

### Dependencies

The development dependency story is a bit messy:

* brew is used to install some tools required by development scripts
* mise is used runtimes, package managers, and runners (direnv + just). Mise should be used to install any tools required for running `build*` and `test*` Justfile recipes but not tools that are *very* popular (like jq, etc).
  * Note that asdf could probably be used instead of mise, but I haven't tested it and there's many Justfile recipes that use mise.
* apt is used to install *some* of the tools required to run CI scripts (like zsh), but some are omitted since they should never run in production.

### DevProd

* There should be no secret scripts. Everything to setup and manage a environment should be within the repo. I've chosen a Justfile for this purpose.

### Deployment

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
* https://github.com/zhanymkanov/fastapi-best-practices