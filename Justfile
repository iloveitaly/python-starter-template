#######################
# Goal of this file:
#
# * No bin/ scripts scattered around the repo
# * All development, CI, and production scripts in one place.
# * No complicated scripts in CI. Include scripts here, run them on GH actions.
# * No hidden magical scripts on developers machines without a place to go
#
#######################

# _ is currently being used a recipe namespace char, use `-` to separate words
# TODO this will be improved later on: https://github.com/casey/just/issues/2442

set shell := ["zsh", "-cu"]
set ignore-comments := true

# for [script]
set unstable := true

default:
	just --list

#######################
# Setup
#######################

# include all development requirements not handled by `mise` for local development
[macos]
requirements:
	@if ! which mise > /dev/null; then \
		echo "mise is not installed. Please install."; \
		echo "https://mise.jdx.dev"; \
		exit 1; \
	fi

	# for procfile management
	@if ! gem list -i foreman >/dev/null 2>&1; then \
		echo "Installing foreman"; \
		gem install foreman; \
	fi

	@if ! which fd > /dev/null; then \
		echo "fd is not installed. Please install."; \
		brew install fd; \
	fi

	@if ! which jq > /dev/null; then \
		echo "jq is not installed. Please install."; \
		brew install jq; \
	fi

# TODO should only be run locally, and not on CI
[macos]
setup: requirements && db_reset
	@if [ ! -f .env.local ]; then \
		cp .env.local-example .env.local; \
		echo "Please edit .env.local to your liking."; \
	fi

	# TODO should check if `layout uv` is supported :/

	# direnv will setup a venv & install packages
	direnv allow .

[macos]
tooling_upgrade:
	brew upgrade jq fd
	gem install foreman
	mise self-update

	# TODO should attempt to upgrade mise versions to the latest versions, this will require some tinkering

[macos]
upgrade: tooling_upgrade js_upgrade py_upgrade

clean:
	rm -rf .nixpacks web/.nixpacks || true
	rm -r tmp/*
	rm -rf web/build
	rm -rf web/node_modules
	rm -rf web/.react-router

#######################
# Javascript
#######################

# TODO .tool-versions update script could be neat for x.x.y

WEB_DIR := "web"
_pnpm := "cd " + WEB_DIR + " && pnpm"

js_setup:
	{{_pnpm}} install

js_nuke: && js_setup
	cd {{WEB_DIR}} && rm -rf node_modules

# TODO support GITHUB_ACTIONS formatting
js_lint:
	{{_pnpm}} prettier --check .
	{{_pnpm}} eslint --cache --cache-location ./node_modules/.cache/eslint .
	{{_pnpm}} depcheck --ignore-bin-package

js_lint-fix:
	{{_pnpm}} prettier --write .
	{{_pnpm}} eslint --cache --cache-location ./node_modules/.cache/eslint . --fix

js_dev:
	[[ -d {{WEB_DIR}}/node_modules ]] || just js_setup
	{{_pnpm}} run dev

js_build: js_setup
	{{_pnpm}} run build

# interactive repl for testing ts
js_playground:
	{{_pnpm}} dlx tsx ./playground.ts

js_upgrade:
	{{_pnpm}} npm-check-updates --interactive

# this same path is referenced in package.json; do not change without updating there too
OPENAPI_JSON_PATH := justfile_directory() / WEB_DIR / "openapi.json"

_js_generate-openapi:
	# js is used to pretty print the output
	# TODO it's unclear to me why the PYTHONPATH is exactly needed here. We could add package=true to the pyproject.toml
	LOG_LEVEL=ERROR PYTHONPATH=. uv run python -c "from app.server import app; import json; print(json.dumps(app.openapi()))" | jq -r . > "{{OPENAPI_JSON_PATH}}"
	{{_pnpm}} openapi

# generate a typescript client from the openapi spec
[doc("Optional flag: --watch")]
js_generate-openapi *flag:
	if {{ if flag == "--watch" { "true" } else { "false" } }}; then; \
		fd --extension=py . | entr -c just _js_generate-openapi; \
	else; \
		just _js_generate-openapi; \
	fi

#######################
# Python
#######################

py_setup:
	uv venv

py_upgrade:
	# https://github.com/astral-sh/uv/issues/6794
	uv sync -U
	git add pyproject.toml uv.lock

py_install-local-packages:
	# TODO I don't think this does what we want, they are wiped out on a uv sync
	uv pip install --upgrade pip
	uv pip install --upgrade --force-reinstall ipython git+https://github.com/iloveitaly/ipdb@support-executables "pdbr[ipython]" rich git+https://github.com/anntzer/ipython-autoimport.git IPythonClipboard ipython_ctrlr_fzf docrepr pyfzf jedi pretty-traceback pre-commit sqlparse debugpy ipython-suggestions datamodel-code-generator funcy-pipe colorama

	source ~/.functions && python-inject-startup

# rebuild the venv from scratch
py_nuke: && py_install-local-packages
	rm -rf .venv
	# reload will recreate the venv and reset VIRTUAL_ENV and friends
	direnv reload
	uv sync

py_dev:
	fastapi dev main.py

# run all linting operations and fail if any fail
py_lint:
	#!/usr/bin/env zsh

	# NOTE this is important: we want all operations to run instead of fail fast
	set -x

	# poetry run autoflake --exclude=migrations --imports=decouple,rich -i -r .
	if [ -n "${GITHUB_ACTIONS:-}" ]; then
		uv tool run ruff check --output-format=github . || exit_code=$?
		uv run pyright --outputjson > pyright_report.json
		# TODO this is a neat trick, we should use it in other places too + document
		jq -r '.generalDiagnostics[] | "::error file=\(.file),line=\(.range.start.line),col=\(.range.start.character)::\(.message)"' < pyright_report.json
	else
		uv tool run ruff check . || exit_code=$?
		uv run pyright || exit_code=$?
	fi

	# TODO https://github.com/fpgmaas/deptry/issues/610#issue-2190147786
	uv tool run deptry --experimental-namespace-package . || exit_code=$?

	if [[ -n "$exit_code" ]]; then
		echo "One or more commands failed"
		exit 1
	fi

	#   run: uv run pytest tests
	#   run: uv run pytest --cov=./

#######################
# Local Container Management
#######################

up: redis_up db_up

down: db_down
	docker compose down

redis_up:
	docker compose up --wait -d redis

db_up:
	docker compose up -d --wait postgres

db_down:
	docker compose down --volumes postgres

#######################
# Database Migrations
#######################

# completely destroy the dev and test databases without runnign migrations
db_reset: db_down db_up
	# dev database is created automatically, but test database is not
	psql $DATABASE_URL -c "CREATE DATABASE test;"

db_migrate:
	alembic upgrade head
	PYTHON_ENV=test alembic upgrade head

db_seed: db_migrate
	python migrations/seed.py
	PYTHON_ENV=test python migrations/seed.py

# db_generate_migration:
# 	@if [ -z "{{MIGRATION_NAME}}" ]; then \
# 		echo "Enter the migration name: "; \
# 		read name; \
# 	else \
# 		name={{MIGRATION_NAME}}; \
# 	fi; \

# 	alembic revision --autogenerate -m "$name"

# destroy and rebuild the database from the ground up
# less intense than nuking the, keeps existing migrations
db_destroy: db_reset db_migrate db_seed

# only for use in early development
db_nuke: db_reset && db_migrate db_seed
	# destroy existing migrations, this is a terrible idea except when you are hacking :)
	rm -rf migrations/versions/* || true
	just db_generate_migration MIGRATION_NAME="initial_commit"

	PYTHON_ENV=test just db:migrate
	PYTHON_ENV=test just db:seed

#######################
# Deployment
#######################

deploy:
	if ! git remote | grep -q dokku; then \
		git remote add dokku dokku@dokku.me:app; \
	fi

	git push dokku main

#######################
# Production Build
#######################


# TODO maybe pull GH actions build and include it
# https://devcenter.heroku.com/articles/dyno-metadata
GIT_DIRTY := `if [ -n "$(git status --porcelain)" ]; then echo "-dirty"; fi`
GIT_SHA := `git rev-parse HEAD` + GIT_DIRTY
GIT_DESCRIPTION := `git log -1 --pretty=%s`
BUILD_CREATED_AT := `date -u +%FT%TZ`
NIXPACKS_BUILD_METADATA := (
	'-e BUILD_COMMIT="' + GIT_SHA + '" ' +
	'-e BUILD_DESCRIPTION="' + GIT_DESCRIPTION + '" ' +
	'-e BUILD_CREATED_AT="' + BUILD_CREATED_AT + '" '
)

JAVASCRIPT_SECRETS_FILE := ".env.production.frontend"
JAVASCRIPT_IMAGE_TAG := IMAGE_NAME + "-javascript:" + GIT_SHA
JAVASCRIPT_CONTAINER_BUILD_DIR := "/app/build/client"
JAVASCRIPT_PRODUCTION_BUILD_DIR := absolute_path("public")

IMAGE_NAME := `basename $(pwd)`
IMAGE_TAG := IMAGE_NAME + ":latest"
PYTHON_BUILD_CMD := "nixpacks build . --name " + IMAGE_NAME + " " + NIXPACKS_BUILD_METADATA

_production_build_assertions:
	#!/usr/bin/env zsh
	set -ue

	# TODO we should abstract out "IS_CI" to some sort of Justfile check :/

	# only run this on CI
	[ ! -z "${GITHUB_ACTIONS:-}" ] || exit 0

	if [ ! -z "{{GIT_DIRTY}}" ]; then \
			echo "Git workspace is dirty! This should never happen on prod" >&2; \
			exit 1; \
	fi

# build the javascript assets by creating an image, building assets inside the container, and then copying them to the host
build_js-assets: _production_build_assertions
	@echo "Building javascript assets..."
	rm -rf "{{JAVASCRIPT_PRODUCTION_BUILD_DIR}}"

	# production assets bundle public "secrets" which are extracted from the environment
	# for this reason, we need to emulate the production environment, then build the assets statically
	nixpacks build {{WEB_DIR}} --name "{{JAVASCRIPT_IMAGE_TAG}}" {{NIXPACKS_BUILD_METADATA}} \
		--build-cmd='pnpm openapi' \
		--start-cmd='pnpm build'

	# we can't just mount /app/build/server with -v since the build process removes the entire /app/build directory
	docker run $(just direnv_export_docker '{{JAVASCRIPT_SECRETS_FILE}}' --params) {{JAVASCRIPT_IMAGE_TAG}}

	# container count check is paranioa around https://github.com/orbstack/orbstack/issues/1568. This could cause issues
	# when testing this functionality out locally

	# NOTE watch out for the escaped 'json .' here!
	container_id=$(docker ps --no-trunc -a --format "{{ '{{ json . }}' }}" | jq -r 'select(.Image == "{{JAVASCRIPT_IMAGE_TAG}}") | .ID') && \
		[ "$(echo "$container_id" | wc -l)" -eq 1 ] || (echo "Expected exactly one container, got $container_id" && exit 1) && \
		docker cp $container_id:{{JAVASCRIPT_CONTAINER_BUILD_DIR}} "{{JAVASCRIPT_PRODUCTION_BUILD_DIR}}" && \
		docker rm $container_id

# build the docker container using nixpacks
build: build_js-assets
	@echo "Building python application..."
	{{PYTHON_BUILD_CMD}}

# dump nixpacks-generated Dockerfile for manual build and production debugging
build_dump:
	{{PYTHON_BUILD_CMD}} --out .

build_clean:
	rm -rf .nixpacks/

# inject a shell where the build fails
build_debug: build_dump
	# store the modified build command in a variable rather than editing the file
	BUILD_DEBUG_CMD=$(sed 's/docker build/BUILDX_EXPERIMENTAL=1 docker buildx debug --invoke bash build/' .nixpacks/build.sh) && eval "$BUILD_DEBUG_CMD"

	# BUILDX_EXPERIMENTAL=1 docker buildx debug --invoke bash build . -f ./.nixpacks/Dockerfile

# instead of using autogenerated Dockerfile, build from the dumped Dockerfile which can be manually modified for development
build_from-dump:
	.nixpacks/build.sh

# open up a bash shell in the last built container, helpful for debugging production builds
build_shell: build
	docker run -it {{IMAGE_TAG}} bash -l

# open up a *second* shell in the *same* container that's already running
build_shell-exec:
	docker exec -it $(docker ps -q --filter "ancestor={{IMAGE_TAG}}") bash -l

# run the container locally, as if it were in production (against production DB, resources, etc)
build_run-as-production procname="":
	# TODO I don't think we want ulimit here, that's just for core dumps, which doesn't seem to work
	# TODO extract local variables from direnv and pass it over the wire
	# TODO memory limits
	docker run -p 8000 $(just direnv_export_docker "" --params) --ulimit core=-1 {{IMAGE_TAG}} "$(just extract_proc "{{procname}}")"

# extract worker start command from Procfile
[script]
extract_proc procname:
  [ -n "{{procname}}" ] || exit 0
  yq -r '.{{procname}}' Procfile

#######################
# Direnv Extensions
#
# Primarily to workout direnv limitations:
# - DIRENV_* vars are always included in the export
# - layout related vars are included as well
# - Path modifications are included
# - There is not an intuitive way to export a specific env file as json
#
# The logic here requires RENDER_DIRENV logic in the top-level .envrc
#
#######################

jq_script := """
with_entries(
	select((
		(.key | startswith("DIRENV") | not)
		and (.key | IN("VIRTUAL_ENV", "VENV_ACTIVE", "UV_ACTIVE", "PATH") | not)
	))
)
"""

# TODO report this upstream to direnv, this is an insane workaround :/
# target a specific .env file (supports direnv features!) for export as a JSON blob
@direnv_export target="":
	([ ! -n "{{target}}" ] || [ -f "{{target}}" ]) || (echo "{{target}} does not exist"; exit 1)
	[ "{{target}}" != ".envrc" ] || (echo "You cannot use .envrc as a target"; exit 1)

	RENDER_DIRENV={{target}} direnv exec ../ direnv export json 2>/dev/null | jq -r '{{jq_script}}'

# export env variables for a particular file in a format docker can consume
[doc("Export as docker '-e' params: --params")]
@direnv_export_docker target *flag:
	if {{ if flag == "--params" { "true" } else { "false" } }}; then; \
		just direnv_export "{{target}}" | jq -r 'to_entries | map("-e \(.key)=\(.value)") | join(" ")'; \
	else; \
		just direnv_export "{{target}}" | jq -r 'to_entries[] | "\(.key)=\(.value)"'; \
	fi