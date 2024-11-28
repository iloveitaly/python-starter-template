# Python & React Router Project Template

This is an extremely opinionated template for a Python and React project. Here's the stack:

* Justfile + Direnv + Mise + Lefthook + Localias + 1Password for local development & secret configuration
* Python + FastAPI + ActiveModel + SQLModel + SQLAlchemy + Alembic + Celery
* TypeScript + React + Vite + React Router (in SPA mode) + ShadCN + Tailwind + ESLint + Prettier + HeyAPI (for OpenAPI)
* Postgres + Redis + Mailpit
  * Docker Compose for running locally
  * Mailpit for local email testing
  * OrbStack is recommended for local docker development for nice automatic domains
* Sentry + Clerk (user manager) + PostHog
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
   3. You get access to the great tooling (static analysis and improved LLM performance) on both Python and JavaScript.
   4. You can move fast with React and all of the amazing UI libraries built on top of it, without having to deal with full stack JavaScript.
   5. You get access to massive JS + Py labor markets.

#3 is what is implemented here.

## Getting Started

There are a couple of dependencies which are not managed by the project:

* [just](https://just.systems)
* [mise](https://mise.jdx.dev)
* docker (or [OrbStack](https://orbstack.dev))

Once you have them installed

```shell
just setup
```

Should do the rest. Note that you'll probably want to install the shell hooks for just, mise, and direnv which you will need to do manually.

## Usage

### Integration Tests

To debug integration tests, you'll want to see what's happening. Use `--headed` to do this:

```
pytd tests/integration/user_creation_test.py -k signup --headed
```

Note that `--headed` *does* change a lot of underlying Chrome parameters which can impact how the browser interacts
with the web page.

If a test fails, a screenshot *and* trace is generated that you can use to replay the session and quickly visually inspect what went wrong.

```
page.pause()
```

## Architecture Notes

notes:
assume injection of pretty traceback
ipython in prod for console exploration
typing from python to typescript via pyright + openapi + typescript library gen
react-router seems to wrap `vite preview`
direnv allow config

### TypeID by Default

<!--

I wouldn't call myself an expert, but I do have opinions on best practices ![:slightly_smiling_face:](https://a.slack-edge.com/production-standard-emoji-assets/14.0/apple-medium/1f642@2x.png) First, yes, I've seen schemas which have an `id` and `ext_id` column for an external ID. But realistically, when stored with postgres's UUID column, it's stored as a 128-bit integer, only twice as big as the usual index column type, and with ULIDs (used by TypeID), the index/locality issue goes away. The biggest issue IMO is the ergonomics of a large, hard-to-memorize ID vs a smaller one. In my assessment, this issue is offset by:

1.  TypeIDs tell you what kind of ID they are
2.  Never getting a bad join (if you join the wrong table, there will be no results, because ulids never collide)
3.  Ability to pregenerate IDs clientside
4.  Eventually sequential IDs get big enough anyways.

Going back to the `id`/`ext_id` approach, the `ext_id` was actually more similar to a youtube video ID, something very compact. So even that came down to the ergonomics. Not sure what exactly you're building, but I'd say 90% of use cases can use ULID TypeIDs on postgres without thinking twice.

-->

### Dependencies

Non-language dependencies are always tricky. Here's how it's handled:

* `brew` is used to install tools required by development scripts
* `mise` is used for runtimes, package managers (uv, pnpm), and runners (direnv + just). Mise should be used to install any tools required for running `build*` and `test*` Justfile recipes but not tools that are *very* popular (like jq, etc) which are better installed by the native os package manager.
  * Note that `asdf` could probably be used instead of `mise`, but I haven't tested it and there's many Justfile recipes that use mise.
* `apt` is used to install *some* of the tools required to run CI scripts (like zsh), but most are omitted since they should never run in production.
* Direct install scripts are used to install some more obscure packages (localias, nixpacks, etc) that are not well supported by the os package manager or mise.

### DevProd

Here are the devprod principles this project adheres to:

* There should be no secret scripts on a developers machine. Everything to setup and manage a environment should be within the repo. I've chosen a Justfile for this purpose.
* The entire lifecycle of a project should be documented in code. Most of the time, this means Justfile recipes.

### Deployment

* Containers should be used instead of proprietary build systems (Heroku, etc).
* Ability to build production-identical containers locally for debugging
* Container building and registry storage should be handled on CI. This reduces vendor lock in.

## Other Project Templates

* https://github.com/peterdresslar/fastapi-sqlmodel-alembic-pg
* https://github.com/fastapi/full-stack-fastapi-template/
* https://github.com/epicweb-dev/epic-stack/blob/main/docs/examples.md
* https://github.com/tierrun/tier-vercel-openai
* https://github.com/shadcn-ui/next-template

## Great Open Source Projects

* https://github.com/danswer-ai/danswer
* https://github.com/developaul/translate-app
* https://github.com/Skyvern-AI/skyvern
* https://github.com/vercel/ai-chatbot
* https://github.com/zhanymkanov/fastapi-best-practices