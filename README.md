# Python & React Router Project Template

This is an extremely opinionated web application template:

1. Full-stack integration tests. This includes HTTPS and production-build JS on CI.
2. Eliminate magic commands. Env vars, developer environments, infra, etc should all be documented in code.
3. Containerized builds.
4. Full-stack typing.
5. Use boring core technology. No fancy databases, no novel languages, no obscure frameworks.

## Tech Stack

Here's the stack:

* **Development lifecycle.** Justfile + Direnv + Mise + Lefthook + Localias + 1Password for local development & secret configuration
* **Backend.** Uv + Ruff + Python + FastAPI + [ActiveModel](https://github.com/iloveitaly/activemodel) + SQLModel + SQLAlchemy + Alembic + Celery + TypeId + Playwright + [Mailers](https://github.com/alex-oleshkevich/mailers)
* **Frontend.** Pnpm + TypeScript + React + Vite + Vitest + React Router (in SPA mode) + ShadCN + Tailwind + ESLint + Prettier + [HeyAPI](https://heyapi.dev)
* **Services.** Postgres + Redis + Mailpit
  * Docker Compose for running locally and on CI
  * Mailpit for local email testing
  * OrbStack is recommended for local docker development for nice automatic domains
* **Observability.** Sentry + Clerk (user management) + PostHog
* **Build.** Docker + nixpacks for containerization
* **CI/CD.** GitHub Actions for CI/CD
* **Deployment.** Up to you: anything that supports a container.

## Cost of Complexity

This is not a simple application template.

There are many things I don't like about this setup. There's a complexity cost and I'm not sure if it's worth it. It's definitely not for the faint of heart and solves very specific problems I've experienced as codebases and teams grow.

Modern web development is all about tradeoffs. Here are the options as I see them:

1. Use Rails, HotWire, etc.
   1. You lose React, all of the amazing ui libraries that come with it, the massive JS + Py labor market, great tooling (formatting, linting, etc), typing (Sorbet is not great), 1st class SDKs for many APIs (playwright, for example), and better trained LLMs.
   2. You get a battle-tested (Shopify! GitHub!) beautifully crafted batteries-included framework.
   3. You get a really beautiful language (I think Ruby is nicer than Python).
2. Use full stack JavaScript/TypeScript.
   1. You have to work with JavaScript everyday. I've given up on backend JavaScript. The whole ecosystem is a mess and I don't enjoy working in it. Non-starter for me. A personal preference and hill I'll die on.
   2. You get access to a massive labor market, great tooling, typing, and well-trained LLMs.
3. Use Python & React.
   1. You lose simplicity. You have to deal with two languages, which means more complex build systems and additional cognitive load.
   2. You lose a single beautifully crafted stack and instead have to stitch together a bunch of different tools (even if they are well-designed independently). Python's ecosystem is mature but not cohesive like Rails (no, Django is not even close).
   3. You get full-stack typing (if you do it right).
   4. You get access to the great tooling ([static analysis](https://astral.sh) and improved LLM performance) on both Python and JavaScript.
   5. You can move fast with React and all of the [amazing](https://ui.shadcn.com) [UI](https://www.chakra-ui.com) libraries built on top of it, without having to deal with full stack JavaScript.
   6. You get access to massive JS + Py labor markets.

This template uses #3.

## Getting Started

There are a couple of dependencies which are not managed by the project:

* zsh. The stack has not been tested extensively on bash.
* [mise](https://mise.jdx.dev)
* docker (or preferably [OrbStack](https://orbstack.dev))
* Latest macOS
* VS Code

(you __could__ use a different setup (bash, vim, etc), but this is not the golden path for this project.)

[Copier](https://copier.readthedocs.io/en/stable/) is the easiest way to get started. It allows you to clone this project, automatically customize the important pieces of it, and most importantly *stay up to date* by pulling upstream changes:

```shell
mkdir your-project

# shell extensions help copier infer github username, etc. Not required if you want to do that yourself.
uv tool run --with jinja2_shell_extension \
  copier copy https://github.com/iloveitaly/python-starter-template . \
  --trust
```

The neat thing about copier is [you can pull updates](.copier/update.sh) from this template later on:

```shell
uv tool run --with jinja2_shell_extension copier update --trust --skip-tasks --skip-answered
```

If you want to skip updates in a particular directory ('web' in this case):

```shell
uv tool run --with jinja2_shell_extension copier update --trust --skip-tasks --skip-answered --exclude web
```

Once you've copied the template and have the above dependencies installed, you can run:

```shell
mise install
just setup
```

That should do most of what you need. Here are some bits you'll need to handle manually:

* [Install the shell hooks for a couple tools](#shell-completions). Direnv is especially important.
* If you use 1password for secrets, [you'll need to set up the 1Password CLI.](https://developer.1password.com/docs/cli/)

### Simple Mode

If you despise dev productivity tooling (no judgement!) you can:

* Avoid using direnv.
* Avoid using 1password.

If you are working on a team, ask a friend who has the system fully configured to run:

```shell
just direnv_bash_export
```

You can simply source the resulting file when you create a new shell session.

The primary downside to this approach is:

* Any mutated API keys from 1Password will not be automatically updated
* Updated ENV configuration will not be automatically used
* You cannot easily

If you are a solo contributor to the project, you'll have to edit the `.envrc` and friends down to a single `.env` which you could manually or use traditional `dotenv` tooling in python and javascript.

### Advanced Mode

There are some extra goodies available if you are adventurous:

```shell
just requirements --extras
```

### Shell Completions

Here are a couple additions to your shell environment that you'll probably want to make:

* [direnv](https://direnv.net/docs/hook.html)
* [mise](https://mise.jdx.dev/cli/completion.html)
* [just](https://just.systems/man/en/shell-completion-scripts.html)
* [fzf tab completion](https://github.com/Aloxaf/fzf-tab) (this makes working with just really nice)

## Usage

### Dependencies

Non-language dependencies are always tricky. Here's how it's handled:

* `brew` is used to install tools required by development scripts
* `mise` is used for runtimes, package managers (uv, pnpm), and runners (direnv + just). Mise should be used to install any tools required for running `build*` and `test*` Justfile recipes but not tools that are *very* popular (like jq, etc) which are better installed by the native os package manager.
  * Note that `asdf` could probably be used instead of `mise`, but I haven't tested it and there's many Justfile recipes that use mise.
* `apt` is used to install *some* of the tools required to run CI scripts (like zsh), but most are omitted since they should never run in production.
* Direct install scripts are used to install some more obscure packages (localias, nixpacks, etc) that are not well supported by the os package manager or mise.

### GitHub Actions

It's helpful, especially when you are conserving GH actions credits and tinkering with your build setup, to sometimes disable GitHub actions.

The easiest way to do this is with the CLI:

```shell
gh workflow disable # and `enable` to turn it back on
```

### Python Factories

I tried both [factoryboy](https://factoryboy.readthedocs.io/en/stable/index.html) and [polyfactory](https://github.com/litestar-org/polyfactory/) and landed on polyfactory for a couple reasons:

- Integration with SQLAlchemy + Pydantic
- Type inference. It looks at the types defined on the pydantic model (including sqlmodel!) and generates correct values for you. This is really nice.

There are some significant gaps in functionality, but the maintainers [have been open to contributions.](https://github.com/litestar-org/polyfactory/pulls?q=is%3Apr+author%3Ailoveitaly)

### Python Debugging Extras

I'm a big fan of lots of installing many debugging tools locally. These should not be installed in the production build.

I've included my favorites in the `debugging-extras` group. These are not required for the project to run.

### Naming Recommendations

General recommendations for naming things throughout the system:

* Longer names are better than shorter names.
* All lowercase GitHub organizations and names. Some systems are case sensitive and some are not.
* All 1password fields should be hyphen-separated and not use spaces.

### Pytest

* [pretty-traceback](https://github.com/mbarkhau/pretty-traceback/pull/17) is used to clean up the horrible-by-default pytest stack traces that make life difficult.
* Since `tests/` is in the top-level of the project, `__init__.py` is required
* All fixtures should go in `conftest.py`. Importing fixtures externally [could break in future versions.](https://docs.pytest.org/en/7.4.x/how-to/fixtures.html#using-fixtures-from-other-projects)

### Migrations

1. SQLModel provides a way to push a model definition into the DB. However, once columns and not tables are mutated you must drop the table and recreate it otherwise changes will not take effect. If you develop in this way, you'll need to be extra careful.
2. If you've been playing with a model locally, you'll want to `just db_reset` and then generate a new migration with `just db_generate_migration`. If you don't do this, your migration may work off of some of the development state.
3. The database must be fully migrated before generating a new migration `just db_migrate` otherwise you will get an error.

### Environment Lifecycle

Across `py`, `js`, and `db` the following subcommands are supported:

* `clean`. Wipe all temporary files related to the environment.
* `setup`. Set up the environment.
* `nuke`. Clean & setup.
* `play`. Interactive playground.
* `lint`. Run linting.
* `lint`-fix. Run linting and fix all errors.
* `test`. Run tests.
* `dev`. Run the development server.

There are top-level commands for many of these (`clean`, `setup`, `dev`, etc) which run actions for all environments.

### Linting

The more linting tools are better, as long as they are well maintained, useful, and add value.

This project implements many linting tools (including DB SQL linting!). This could cause developer friction at some point, but we'll see how this scales as the codebase complexity grows.

### Test Database Cleaning

This is implemented by `activemodel` which is a package created specifically for this project.

Two methods are needed:

* Transaction. Used whenever possible. If you create customize secondary engines outside the context of `activemodel` this will break.
* Truncation. Transaction-based cleaning does not work is database mutations occur in a separate process.
  * This gets tricky because of platform differences between macOS and Linux, but the tldr is although it's possible to share a DB session handle between the test process *and* the uvicorn server running during integration tests, it's a bad idea with lots of footguns, so we opt for truncation.

### General Testing Architecture

Here's how this project thinks about tests:

* The test environment should mirror production as closely as possible and for higher level tests (integration or smoke tests) we should put in extra engineering effort to get there. Accept additional complexity in integration tests to mirror the production environment more closely.
* All core application workflows should be covered with an integration test. I think of an integration test as a browser-based test using production-built javascript/HTML.
* Most common flows should be covered by a functional test. I think of a functional test as e2e tests on specific API routes or jobs. Primarily testing backend logic and not interaction with the UI.
* Unit tests should be used for tricky code or to validate regressions.

### Integration Testing (Playwright)

Everyone calls integration testing something different. To me, integration tests are:

* Few in number, since they are expensive, slow, and brittle.
* Use the production configuration as much as possible. This means production JS build, HTTPS, etc.
* Cover the main workflows of the application to provide automated QA against the most important pieces of the application.
* Provide self-documentation about what the system does.

Here are some tips for working with the Playwright integration tests.

Log the DOM structure:

```python
screen.debug()
```

Pause playwright execution:

```python
page.pause()
```

### 'Login As' Admin Functionality

This is an important part of any production application. Being able to impersonate a user and view their application to debug issues.

* The user table has a role field
* After logging in, set the user to `admin` and you'll be able to switch users.

### React Router Routes

Here's a more complex example of how to define nested routes + layouts in react router 7:

```typescript
import type { RouteConfig } from "@react-router/dev/routes"
import { index, layout, prefix, route } from "@react-router/dev/routes"

export default [
  index("routes/index.tsx"),
  layout("layouts/authenticated.tsx", [
    ...prefix("intake", [
      layout("layouts/intake.tsx", [
        index("routes/intake/index.tsx"),
        route("/:id", "routes/intake/detail.tsx"),
      ]),
    ]),
    ...prefix("notes", [
      layout("layouts/notes.tsx", [
        index("routes/notes/index.tsx"),
        route(":id", "routes/notes/detail.tsx"),
      ]),
    ]),
    route("/settings", "routes/settings.tsx"),
  ]),
] satisfies RouteConfig
```

The `routes.ts` is meant to be a simple way to define routes configuration at a high level.
Unlike previous react router versions, loaders and other options are not available.

[We have a special handler in fastapi](app/routes/static.py) to serve the JS files when any route not defined explicitly
by FastAPI is requested. A "better" (and more complex) way to handle this is to deploy JS assets to a CDN and use a
separate subdomain for the API server. Keeping everything in a single docker container and application is easier
on deployment.

### Debugging Javascript Vite Build

Here's how to use `debugger` statements within vite code:

```shell
VITE_BUILD_COMMIT=-dirty node inspect web/node_modules/@react-router/dev/bin.js build
```

### Cookies & Sessions

* The FastAPI session middleware is setup so you can use cookies/sessions in your project.
* Subdomains are used for the API server instead of separate domains in test, so cookies can be shared between the API server and the web client.
* `same-origin` cookies are enforced in prod, but not in dev.

### Pytest Route Tests

* Use `api_app.url_path_for` for all URL generation.

### Pytest Integration Playwright Tests

<!-- TODO should merge with the section above -->

To debug integration tests, you'll want to see what's happening. Use `--headed` to do this:

```shell
pytd tests/integration/user_creation_test.py -k signup --headed
```

(find [pytd definition here](https://github.com/iloveitaly/dotfiles/blob/a4bd6c2c8f38b1f980fdb878bbf21c27918a5d05/.aliases#L98))

Note that `--headed` *does* change a lot of underlying Chrome parameters which can impact how the browser interacts
with the web page.

If a test fails, a screenshot *and* trace is generated that you can use to replay the session and quickly visually inspect what went wrong.

Instead of `breakpoint()` use this to debug and test the page:

```python
page.pause()
```

<!--
## Architecture Notes

notes:
assume injection of pretty traceback
ipython in prod for console exploration
typing from python to typescript via pyright + openapi + typescript library gen
react-router seems to wrap `vite preview`
direnv allow config
-->

### TypeID by Default

From my time at Stripe, I became a big fan of IDs with metadata about the object they represent. There's a great project, TypeID, which has implemented this across a bunch of languages. I've adopted it here.

<!--

I wouldn't call myself an expert, but I do have opinions on best practices ![:slightly_smiling_face:](https://a.slack-edge.com/production-standard-emoji-assets/14.0/apple-medium/1f642@2x.png) First, yes, I've seen schemas which have an `id` and `ext_id` column for an external ID. But realistically, when stored with postgres's UUID column, it's stored as a 128-bit integer, only twice as big as the usual index column type, and with ULIDs (used by TypeID), the index/locality issue goes away. The biggest issue IMO is the ergonomics of a large, hard-to-memorize ID vs a smaller one. In my assessment, this issue is offset by:

1.  TypeIDs tell you what kind of ID they are
2.  Never getting a bad join (if you join the wrong table, there will be no results, because uuids never collide)
3.  Ability to pregenerate IDs clientside
4.  Eventually sequential IDs get big enough anyways.

Going back to the `id`/`ext_id` approach, the `ext_id` was actually more similar to a youtube video ID, something very compact. So even that came down to the ergonomics. Not sure what exactly you're building, but I'd say 90% of use cases can use ULID TypeIDs on postgres without thinking twice.

-->

### Secrets

The secret management is more complex that it seems like it should be. The primary reason behind this is to avoid secret
drift at all costs. Here's why:

* Different developers have *slightly* different secrets that create a "works on my machine" problem.
* New secrets are not automatically integrated into local (or CI) environments causing the project to break when a new
  environment variable is introduced.
* Cumbersome and undocumented CI & production secret management. I want a single command to set secrets on CI & prod
  without any thinking or manual intervention.

Solving these problems adds more complexity to the developer experience. We'll see if it's worth it.

Secret management is handled in a couple of different places:

* `.env*` files which source secrets from 1password using `op read`
* `just secrets_*` which generate 1password connection tokens and set them on CI

Most likely, you'll need to bootstrap your secret management by manually setting your account + vault
in order to generate a connection token:

```shell
OP_ACCOUNT=company.1password.com OP_VAULT_UID=a_uuid just secrets_local-service-token
```

And drop the resulting token in your `.env.local` file.

### DevProd

Here are the devprod principles this project adheres to:

* There should be no secret scripts on a developers machine. Everything to setup and manage a environment should be within the repo. I've chosen a Justfile for this purpose.
* The entire lifecycle of a project should be documented in code. Most of the time, this means Justfile recipes.

### Deployment

* Containers should be used instead of proprietary build systems (Heroku, etc).
* Ability to build production-identical containers locally for debugging
* Container building and registry storage should be handled on CI. This reduces vendor lock in.

### Python Job Queue

I tried both RQ and Celery, and looked at other job queue systems, before landing on Celery.

#### Celery

* Job scheduling is handled in the same process as job execution, which is a terrible idea in large-scale systems.

#### RQ

I *really* liked the idea of [RQ as a job queue](https://python-rq.org). The configuration and usage seemed much more simple.

However, it didn't work for me.

* [Did not work on macOS](https://github.com/rq/rq/issues/2058)
* [Spawn workers were not supported](https://github.com/rq/rq/pull/2176) and I ran into strange issues when running subprocesses.
* The fastapi dashboard is pretty terrible. I don't want to waste time building a dashboard.
* There is no exponential backoff built in.

At this point, I gave up trying and switched to celery. The big downside with celery is there's no way to run Flower
inside an existing application (you can't bolt it on to a fastapi server) so you'll need an entirely separate container
running the flower application.

Here's the Procfile command that worked for RQ:

```yml
worker: rq worker --with-scheduler -w rq.worker.SpawnWorker
```

[I've left some of the configuration around](./app/rq.py) in case you want to try it out.

## Production

### Frontend

* `window.SENTRY_RELEASE` has the commit sha of the build.
* Backend uses JSON logging in production
* `devDependencies` should only contain dependencies that are required for local development. All dependencies required
  for building the frontend should be in `dependencies`.

## Related

### Other Templates

Some other templates I ran across when developing this project:

* https://github.com/peterdresslar/fastapi-sqlmodel-alembic-pg
* https://github.com/fastapi/full-stack-fastapi-template/
* https://github.com/epicweb-dev/epic-stack/blob/main/docs/examples.md
* https://github.com/tierrun/tier-vercel-openai
* https://github.com/shadcn-ui/next-template
* https://github.com/albertomh/pycliche

### Great Open Source Projects

Great for grepping and investigating patterns.

#### Python

* https://github.com/danswer-ai/danswer
* https://github.com/developaul/translate-app
* https://github.com/Skyvern-AI/skyvern
* https://github.com/zhanymkanov/fastapi-best-practices
* https://github.com/bartfeenstra/betty
* https://github.com/AlexanderZharyuk/billing-service
* https://github.com/replicate/cog
* https://github.com/Kludex/awesome-fastapi-projects

#### Javascript/Remix/React Router

* https://github.com/vercel/ai-chatbot
