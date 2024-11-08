# _ is currently being used a recipe namespace char, use `-` to separate words
# TODO this will be improved later on: https://github.com/casey/just/issues/2442

set shell := ["zsh", "-cu"]

default:
  just --list

# TODO should adjust for new mise config with additional tooling
# include development-specific requirements here
requirements:
	# for procfile management
	@if ! gem list -i foreman >/dev/null 2>&1; then \
		echo "Installing foreman"; \
		gem install foreman; \
	fi

	@if ! which direnv > /dev/null; then \
			echo "direnv is not installed. Please install."; \
			exit 1; \
	fi

	@if ! which uv > /dev/null; then \
			echo "uv is not installed. Please install."; \
			exit 1; \
	fi

tooling_upgrade:
  echo "updating tooling"

upgrade: js_upgrade py_upgrade tooling_upgrade

# TODO should only be run locally, and not on CI
setup: requirements && db_reset
	@if [ ! -f .env.local ]; then \
		cp .env.local-example .env.local; \
	fi

	# direnv will setup a venv & install packages
	direnv allow .

up: redis_up db_up

#######################
# Javascript
#######################

# TODO .tool-versions update script could be neat for x.x.y

WEB_DIR := "web"
_pnpm := "cd " + WEB_DIR + " && pnpm"

# TODO support GITHUB_ACTIONS formatting
js_lint:
	{{_pnpm}} prettier --check .
	{{_pnpm}} eslint --cache --cache-location ./node_modules/.cache/eslint .
	{{_pnpm}} depcheck --ignore-bin-package

js_lint-fix:
	cd {{WEB_DIR}} && pnpx prettier --write .
	cd {{WEB_DIR}} && pnpx eslint --cache --cache-location ./node_modules/.cache/eslint . --fix

js_dev:
	[[ -d {{WEB_DIR}}/node_modules ]] || just js_setup
	{{_pnpm}} run dev

js_build: js_setup
	{{_pnpm}} run build

# interactive repl for testing ts
js_playground:
	{{_pnpm}} dlx tsx ./playground.ts

js_setup:
	{{_pnpm}} install

js_nuke: && js_setup
	cd {{WEB_DIR}} && rm -rf node_modules

js_upgrade:
	{{_pnpm}} npm-check-updates --interactive

# maybe use watch + entr here?
js_generate-openapi:
	# TODO should fail if server is not running, should pull from a domain vs port
	http --pretty=format localhost:8000/openapi.json > tmp/openapi.json
	pnpx @hey-api/openapi-ts -i tmp/openapi.json -o web/client -c @hey-api/client-fetch

#######################
# Python
#######################

py_setup:
	uv venv

py_upgrade:
	# https://github.com/astral-sh/uv/issues/6794
	uv sync -U

py_install-local-packages:
	uv pip install --upgrade pip
	uv pip install --upgrade --force-reinstall ipython git+https://github.com/iloveitaly/ipdb@support-executables "pdbr[ipython]" rich git+https://github.com/anntzer/ipython-autoimport.git IPythonClipboard ipython_ctrlr_fzf docrepr pyfzf jedi pretty-traceback pre-commit sqlparse debugpy ipython-suggestions datamodel-code-generator funcy-pipe colorama

	source ~/.functions && python-inject-startup

# rebuild the venv from scratch
py_nuke: && py_install-local-packages
	rm -rf .venv
	direnv reload
	uv sync

py_dev:
  fastapi dev main.py

# run all linting operations and fail if any fail
py_lint:
	#!/usr/bin/env zsh
	set -x

	# poetry run autoflake --exclude=migrations --imports=decouple,rich -i -r .
	if [ -n "$GITHUB_ACTIONS" ]; then
		uv tool run ruff check --output-format=github . || exit_code=$?
		uv run pyright --outputjson > pyright_report.json
		# TODO this is a neat trick, we should use it in other places too + document
		jq -r '.generalDiagnostics[] | "::error file=\(.file),line=\(.range.start.line),col=\(.range.start.character)::\(.message)"' < pyright_report.json
	else
		uv tool run ruff check . || exit_code=$?
		uv run pyright || exit_code=$?
	fi

	# TODO https://github.com/fpgmaas/deptry/issues/610#issue-2190147786
	uv tool run deptry . || exit_code=$?

	if [[ -n "$exit_code" ]]; then
		echo "One or more commands failed"
		exit 1
	fi

	#   run: uv run pytest tests
	#   run: uv run pytest --cov=./

#######################
# Redis
#######################

redis_up:
	docker compose up --wait -d redis

#######################
# Database Migrations
#######################

db_up:
	docker compose up -d --wait postgres

db_down:
	docker compose down --volumes postgres

db_reset: db_down db_up
	psql $DATABASE_URL -c "CREATE DATABASE test;"

db_migrate:
	alembic upgrade head
	PYTHON_ENV=test alembic upgrade head

db_seed: db_migrate
	python migrations/seed.py
	PYTHON_ENV=test python migrations/seed.py

db_generate_migration:
	@if [ -z "$${MIGRATION_NAME}" ]; then \
		echo "Enter the migration name: "; \
		read name; \
	else \
		name=$${MIGRATION_NAME}; \
	fi; \

	alembic revision --autogenerate -m "$$name"

# destroy and rebuild the database from the ground up
# less intense than nuking the, keeps existing migrations
db_destroy: db_reset db_migrate db_seed

# only for use in early development :)
db_nuke: db_reset && db_migrate db_seed
	# destroy existing migrations, this is a terrible idea except when you are hacking :)
	rm -rf migrations/versions/* || true
	just db:generate:migration MIGRATION_NAME="initial_commit"

	PYTHON_ENV=test just db:migrate
	PYTHON_ENV=test just db:seed

#######################
# Production Build
#######################

IMAGE_NAME := `basename $(pwd)`
IMAGE_TAG := "latest"
BUILD_CMD := "nixpacks build . --name " + IMAGE_NAME + " --tag " + IMAGE_TAG

deploy:
	if ! git remote | grep -q dokku; then \
		git remote add dokku dokku@dokku.me:app; \
	fi

	git push dokku main

# build the docker container using nixpacks
build:
	{{BUILD_CMD}}

build_clean:
	rm -rf .nixpacks/

# dump nixpacks-generated Dockerfile for manual build and production debugging
build_dump:
	{{BUILD_CMD}} --out .

# inject a shell where the build fails
build_debug: build_dump
	# store the modified build command in a variable rather than editing the file
	BUILD_DEBUG_CMD=$(sed 's/docker build/BUILDX_EXPERIMENTAL=1 docker buildx debug --invoke bash build/' .nixpacks/build.sh) && eval "$BUILD_DEBUG_CMD"

	# BUILDX_EXPERIMENTAL=1 docker buildx debug --invoke bash build . -f ./.nixpacks/Dockerfile

# instead of using autogenerated Dockerfile, build from the dumped Dockerfile which can be manually modified
build_from-dump:
	# docker build . -f ./.nixpacks/Dockerfile -t $(IMAGE_NAME):$(IMAGE_TAG)
	.nixpacks/build.sh

# open up a bash shell in the last built container, helpful for debugging production builds
build_shell: build
	docker run -it {{IMAGE_NAME}}:{{IMAGE_TAG}} bash -l

# open up a *second* shell in the *same* container that's already running
build_shell-exec:
	docker exec -it $(shell docker ps -q -f ancestor=$(IMAGE_NAME):$(IMAGE_TAG)) bash -l

# run the container locally, as if it were in production (against production DB, resources, etc)
build_run-as-production:
	# TODO I don't think we want ulimit here, that's just for core dumps, which doesn't seem to work
	docker run --ulimit core=-1 --network=host -e LOG_LEVEL=DEBUG -e DATABASE_URL="$$DATABASE_URL" -e REDIS_URL="$$REDIS_URL" -e OPENAI_API_KEY="$$OPENAI_API_KEY" -e SENTRY_DSN="" $(IMAGE_NAME):$(IMAGE_TAG)

clean:
	rm -rf .nixpacks || true
	rm -r tmp/*
	rm -rf web/build
	rm -rf web/node_modules
	rm -rf web/.react-router