#######################
# Goal of this file:
#
# * No bin/ scripts scattered around the repo
# * All development, CI, and production scripts in one place.
# * No complicated scripts in CI. Include scripts here, run them on GH actions.
# * No hidden magical scripts on developers machines without a place to go
# * All ENV variables should be handled via direnv and not configured here
# * Any python code which is not completely independent of the project, should be in app/ so
#   refactoring tools can rename all symbols automatically.
#
#######################

# _ is currently being used a recipe namespace char, use `-` to separate words
# TODO this will be improved later on: https://github.com/casey/just/issues/2442

set shell := ["zsh", "-cu"]
set ignore-comments := true

# for [script] support
set unstable := true

# determines what shell to use for [script]
set script-interpreter := ["zsh", "-euBh"]

# used for image name, op vault access, etc
PROJECT_NAME := `basename $(pwd)`

default:
	just --list

#######################
# Setup
#######################

# TODO should cask install 1password-cli
BREW_PACKAGES := "lefthook jq fd localias nixpacks"

[macos]
[script]
_brew_check_and_install brew_target:
	if ! which {{brew_target}} > /dev/null; then
		echo "{{brew_target}} is not installed. Installing..."
		brew install {{brew_target}}
	fi

# include all development requirements not handled by `mise` for local development
[macos]
[doc("--extras to install non-essential productivity tooling")]
requirements *flags:
	@if ! which mise > /dev/null; then \
		echo "mise is not installed. Please install."; \
		echo "  => https://mise.jdx.dev"; \
		exit 1; \
	fi

	# for procfile management
	# TODO maybe use? https://github.com/yukihirop/ultraman?tab=readme-ov-file
	@if ! gem list -i foreman >/dev/null 2>&1; then \
		echo "Installing foreman"; \
		gem install foreman; \
	fi

	@for brew_package in {{BREW_PACKAGES}}; do \
		just _brew_check_and_install $brew_package; \
	done

	@if ! which commitlint > /dev/null; then \
		if ! cargo --list | grep -q binstall; then \
			echo "cargo binstall not available, skipping commitlint installation"; \
		fi && \
		cargo binstall -y commitlint-rs; \
	fi

	if [[ "{{flags}}" =~ "--extras" ]]; then \
		uv tool add aiautocommit; \
	fi

	lefthook install

	# sample scripts make the hooks dir look pretty messy
	rm .git/hooks/*.sample || true

# setup everything you need for local development
[macos]
setup: requirements && py_setup js_setup db_reset local-alias
	@if [ ! -f .env.local ]; then \
		cp .env.local-example .env.local; \
		echo "Please edit .env.local to your liking."; \
	fi

	# direnv will setup a venv & install packages
	direnv allow .

# TODO should change the CURRENT_BASE for py and other x.x.y upgrades
[script]
[macos]
_mise_upgrade:
	# Get current tools and versions from local .tool-versions only
	TOOLS=("${(@f)$(mise list --current --json | jq -r --arg PWD "$PWD" 'to_entries | map(select(.value[0].source.path == $PWD + "/.tool-versions")) | from_entries | keys[]')}")

	for TOOL in $TOOLS; do
			# Get current version
			CURRENT=$(mise list --current --json | jq -r --arg TOOL "$TOOL" --arg PWD "$PWD" 'to_entries | map(select(.value[0].source.path == $PWD + "/.tool-versions")) | from_entries | .[$TOOL][0].version')
			echo "Current version of $TOOL: $CURRENT"

			# Extract major version
			CURRENT_BASE=$(echo $CURRENT | cut -d. -f1)
			echo "Current base version of $TOOL: $CURRENT_BASE"

			# Get latest version matching current major.minor
			LATEST=$(mise ls-remote "$TOOL" | grep -E "^${CURRENT_BASE}\.[0-9.]+$" | sort -V | tail -n1)

			if [[ -n $LATEST && $CURRENT != $LATEST ]]; then
					sed -i '' "s/^$TOOL .*/$TOOL $LATEST/" .tool-versions
					echo "Updated $TOOL: $CURRENT -> $LATEST"
			fi
	done

	mise install
	git add .tool-versions

# upgrade mise, language versions, and essential packages
[macos]
tooling_upgrade: && _mise_upgrade js_sync-engine-versions
	mise self-update
	HOMEBREW_NO_AUTO_UPDATE=1 brew upgrade {{BREW_PACKAGES}}
	gem install foreman

# upgrade everything: all packages on all languages, tooling, etc
[macos]
upgrade: tooling_upgrade js_upgrade py_upgrade

# run daemon to setup local development aliases
[macos]
[script]
local-alias:
	if [[ "$(localias status)" == "daemon running with pid "* ]]; then
		echo "Daemon already running"
		localias reload
		exit 0
	fi

	localias start

	localias debug config --print

clean: js_clean py_clean build_clean
	rm -rf tmp/* || true
	rm -rf .git/hooks/* || true

#######################
# Javascript
#######################

WEB_DIR := "web"
_pnpm := "cd " + WEB_DIR + " && pnpm"

js_setup:
	{{_pnpm}} install
	{{_pnpm}} run openapi
	{{_pnpm}} react-router typegen

js_clean:
	rm -rf {{WEB_DIR}}/build {{WEB_DIR}}/client {{WEB_DIR}}/node_modules {{WEB_DIR}}/.react-router || true

# TODO support GITHUB_ACTIONS/CI formatting
js_lint +FILES=".":
	{{_pnpm}} prettier --check {{FILES}}
	{{_pnpm}} eslint --cache --cache-location ./node_modules/.cache/eslint {{FILES}}

	# TODO reenable once we have the ui side of things working
	# {{_pnpm}} depcheck --ignore-bin-package

js_lint-fix:
	{{_pnpm}} prettier --write .
	{{_pnpm}} eslint --cache --cache-location ./node_modules/.cache/eslint . --fix

# run tests in the exact same environment that will be used on CI
[script]
js_test:
	# NOTE vitest automatically will detect GITHUB_ACTIONS and change the output format
	# CI=true *will* impact how various JS tooling is run
	if [[ -n "${CI:-}" ]]; then
		{{_pnpm}} vitest run
	else
		cd {{WEB_DIR}} && CI=true direnv exec . pnpm vitest run
	fi

js_dev:
	[[ -d {{WEB_DIR}}/node_modules ]] || just js_setup
	{{_pnpm}} run dev

js_build: js_setup
	# as you'd expect, the `web/build` directory is wiped on each run
	export VITE_BUILD_COMMIT="{{GIT_SHA}}" && {{_pnpm}} run build

# interactive repl for testing ts
js_playground:
	{{_pnpm}} dlx tsx ./playground.ts

# interactively upgrade all js packages
js_upgrade:
	{{_pnpm}} dlx npm-check-updates --interactive && \
		git add package.json pnpm-lock.yaml

# generate a typescript client from the openapi spec
[doc("Optional flag: --watch")]
js_generate-openapi *flag:
	if {{ if flag == "--watch" { "true" } else { "false" } }}; then; \
		fd --extension=py . | entr -c just _js_generate-openapi; \
	else; \
		just _js_generate-openapi; \
	fi

_js_generate-openapi:
	# jq is here to pretty print the output
	LOG_LEVEL=error uv run python -m app.server | jq -r . > "$OPENAPI_JSON_PATH"

	# generate the js client
	{{_pnpm}} openapi

JAVASCRIPT_PACKAGE_JSON := WEB_DIR / "package.json"

# update package.json engines to match the current versions in .tool-versions
[macos]
[script]
js_sync-engine-versions:
	NODE_VERSION=$(mise list --current --json | jq -r ".node[0].version")
	PNPM_VERSION=$(pnpm -v)

	# jq does not have edit in place
	# https://stackoverflow.com/questions/36565295/jq-to-replace-text-directly-on-file-like-sed-i
	tmp_package=$(mktemp)

	jq "
		. + {
			engines: {
				node: \">=$NODE_VERSION\",
				pnpm: \">=$PNPM_VERSION\"
			}
	}" "{{JAVASCRIPT_PACKAGE_JSON}}" > "$tmp_package"

	mv "$tmp_package" "{{JAVASCRIPT_PACKAGE_JSON}}"

#######################
# Python
#######################

# create venv and install packages
py_setup:
	[ -d ".venv" ] || uv venv

	# don't include debugging-extras on CI
	if [ -z "$CI" ]; then \
		uv sync --group=debugging-extras; \
	else \
		uv sync; \
	fi

	# important for CI to install browsers for playwright
	# the installation process is fast enough (<10s) to eliminate the need for attempting to cache via GHA
	# if this turns out not to be true, we should implement: https://github.com/hirasso/thumbhash-custom-element/blob/main/.github/workflows/tests.yml
	uv run playwright install chromium

# clean entire py project without rebuilding
py_clean:
	rm -rf .pytest_cache .ruff_cache .venv

	# pycache should never appear because of PYTHON* vars
	# TODO I wonder if this is happening because of djlint

# rebuild the venv from scratch
py_nuke: py_clean && py_setup
	# reload will recreate the venv and reset VIRTUAL_ENV and friends
	direnv reload

py_upgrade:
	# https://github.com/astral-sh/uv/issues/6794
	uv sync -U --group=debugging-extras
	uv tool upgrade --all
	git add pyproject.toml uv.lock


# open up a development server
py_dev:
	fastapi dev --port $PYTHON_SERVER_PORT

# TODO should have additional tool for workers and all server processes

# TODO add djlint for jinja templates
# run all linting operations and fail if any fail
[script]
py_lint +FILES=".":
	# NOTE this is important: we want all operations to run instead of fail fast
	set -x

	# poetry run autoflake --exclude=migrations --imports=decouple,rich -i -r .
	if [ -n "${CI:-}" ]; then
		# TODO I'm surprised that ruff doesn't auto detect github...
		uv tool run ruff check --output-format=github {{FILES}} || exit_code=$?
		uv run pyright {{FILES}} --outputjson > pyright_report.json || exit_code=$?
		# TODO this is a neat trick, we should use it in other places too + document
		# https://docs.github.com/en/actions/writing-workflows/choosing-what-your-workflow-does/workflow-commands-for-github-actions#setting-a-warning-message
		# https://github.com/jakebailey/pyright-action/blob/b7d7f8e5e5f195796c6f3f0b471a761a115d3b2c/src/main.ts#L62
		jq -r '.generalDiagnostics[] | "::\(.severity) file=\(.file),line=\(.range.start.line),endLine=\(.range.end.line),col=\(.range.start.character),endColumn=\(.range.end.character)::\(.message)"' < pyright_report.json
		rm pyright_report.json
	else
		uv tool run ruff check {{FILES}} || exit_code=$?
		uv run pyright {{FILES}} || exit_code=$?
	fi

	# TODO https://github.com/fpgmaas/deptry/issues/610#issue-2190147786
	# TODO https://github.com/fpgmaas/deptry/issues/740
	# uv tool run deptry --experimental-namespace-package . || exit_code=$?

	if [[ -n "${exit_code:-}" ]]; then
		echo "One or more commands failed"
		exit 1
	fi

# run tests with the exact same environment that will be used on CI
[script]
py_test:
	# integration tests should mimic production as closely as possible
	# to do this, we build the app and serve it like it will be served in production
	just js_build

	# TODO what about code coverage? --cov?
	if [[ -n "${CI:-}" ]]; then
		uv run pytest
	else
		CI=true direnv exec . uv run pytest
	fi

# automatically fix linting errors
py_lint_fix:
	# TODO anything we can do here with pyright?
	uv tool run ruff check . --fix

# record playwright interactions for integration tests and dump them to a file
[macos]
[script]
py_playwright:
	mkdir -p tmp/playwright
	recorded_interaction=tmp/playwright/$(date +%m-%d-%s).py

	uv run playwright codegen --target python-pytest --output $recorded_interaction https://${JAVASCRIPT_SERVER_HOST}

	echo $recorded_interaction
	pbcopy < $recorded_interaction

#######################
# Dev Container Management
#######################

up:
	docker compose up -d --wait

down: db_down
	docker compose down

# separate task for the db to support db_reset
db_up:
	docker compose up -d --wait postgres

# turn off the database *and* completely remove the data
db_down:
	docker compose down --volumes postgres

#######################
# Database Migrations
#######################

# completely destroy the dev and test databases without running migrations
db_reset: db_down db_up

db_lint:
	uv run alembic check

# open the database in the default macos GUI
[macos]
db_open:
	open $DATABASE_URL

# nice tui to interact with the database
[macos]
db_cli:
	uv tool run pgcli $DATABASE_URL

# TODO should I use CI=true with direnv instead of PYTHON_ENV=test?

[script]
db_migrate:
	# dev database is created automatically, but test database is not
	psql $DATABASE_URL -c "CREATE DATABASE ${TEST_DATABASE_NAME};"

	uv run alembic upgrade head
	[ -n "${CI:-}" ] || PYTHON_ENV=test uv run alembic upgrade head

db_seed: db_migrate
	uv run python migrations/seed.py
	[ -n "${CI:-}" ] || PYTHON_ENV=test uv run python migrations/seed.py

# generate migration based on the current state of the database
[script]
db_generate_migration migration_name="":
	if [ -z "{{migration_name}}" ]; then
		echo "Enter the migration name: "
		read name
	else
		name={{migration_name}}
	fi

	uv run alembic revision --autogenerate -m "$name"

# destroy and rebuild the database from the ground up
db_destroy: db_reset db_migrate db_seed

# destroy all migrations and rebuild everything: only for use in early development
db_nuke: db_reset && db_migrate db_seed
	# destroy existing migrations, this is a terrible idea except when you are hacking :)
	# I personally hate having a nearly greenfield project with a thousand migrations when you're iterating on the database schema.
	rm -rf migrations/versions/* || true
	just db_generate_migration "initial_commit"

	# PYTHON_ENV=test just db_migrate
	# PYTHON_ENV=test just db_seed

#######################
# Secrets
#######################

# grant GH actions access to the 1p vault, this needs to be done every 90d
[macos]
[script]
secrets_ci_grant-github-actions:
	# 90d is the max expiration time allowed
	# this can be safely run multiple times, it will not regenerate the service account token
	service_account_token=$(op service-account create {{PROJECT_NAME}}-github-actions \
		 --expires-in '90d' \
		 --vault "${OP_VAULT_UID}:read_items" \
		 --raw \
	)

	gh secret set OP_SERVICE_ACCOUNT_TOKEN --app actions --body "$service_account_token"

# dump direnv configuration into a special file to be accessible to all CI actions
secrets_ci_configure:
	direnv allow . && direnv export gha >> "$GITHUB_ENV"
	# you cannot source GITHUB_ENV, it uses a syntax which is *just* different enough from the shell that it fails
	direnv export json | just secrets_ci_mask

# cannot be run at the same time as configuration
secrets_ci_mask:
	#!/usr/bin/env python
	import json
	import re
	import sys

	# Define the patterns to match specific types of values
	patterns = [
			re.compile(r'sk-\S+'),  # Matches sk-* values
			re.compile(r'https://\S+@o\d+\.ingest\.us\.sentry\.io/\S+'),  # Matches the Sentry DSN pattern
			re.compile(r'sk_\S+'),  # Matches sk_* values
			re.compile(r'phc_\S+')  # Matches phc-* values
	]

	# Define suffixes to detect keys to mask
	key_suffixes = ['_KEY', '_TOKEN', '_SECRET', '_PASSWORD', '_DSN']

	def add_mask(value):
			print(f'::add-mask::{value}')

	# Read JSON from stdin
	env_vars = json.load(sys.stdin)

	# Iterate over all variables from JSON input
	for key, value in env_vars.items():
			# Check if the value matches any of the defined patterns
			if any(pattern.match(str(value)) for pattern in patterns):
					add_mask(str(value))
					continue

			# Check if the key ends with any of the defined suffixes
			if any(key.endswith(suffix) for suffix in key_suffixes):
					add_mask(str(value))
					continue

			# Check if the key starts with OP_ or DIRENV_
			if key.startswith('OP_') or key.startswith('DIRENV_'):
					add_mask(str(value))

# manage the service account from the web ui
[macos]
secrets_ci_manage:
	# you cannot revoke/delete a service account with the cli, you must login and delete it from the web ui
	open https://$OP_ACCOUNT/developer-tools/directory


#######################
# Deployment
#######################

deploy:
	if ! git remote | grep -q dokku; then \
		git remote add dokku dokku@dokku.me:app; \
	fi

	git push dokku main

	# TODO can we push from the registry image?

# TODO fly deployment

#######################
# Production Build
#
# Some of the ENV variables and labels below are pulled from these projects:
#
#   - https://github.com/iloveitaly/github-action-nixpacks/blob/2ad8c4fab7059ede8b6103f17b2ec23f42961fd9/entrypoint.sh
#   - https://devcenter.heroku.com/articles/dyno-metadata
#
#######################

GIT_DIRTY := `if [ -n "$(git status --porcelain)" ]; then echo "-dirty"; fi`
GIT_SHA := `git rev-parse HEAD` + GIT_DIRTY
GIT_DESCRIPTION := `git log -1 --pretty=%s`
BUILD_CREATED_AT := `date -u +%FT%TZ`
NIXPACKS_BUILD_METADATA := (
	'-e BUILD_COMMIT="' + GIT_SHA + '" ' +
	'-e BUILD_DESCRIPTION="' + GIT_DESCRIPTION + '" ' +
	'-e BUILD_CREATED_AT="' + BUILD_CREATED_AT + '" '
)

# .env file without any secrets that should exist on all environments
SHARED_ENV_FILE := ".env"

# .env file with production variables, no secrets, for python
PYTHON_PRODUCTION_ENV_FILE := ".env.production.backend"

JAVASCRIPT_SECRETS_FILE := ".env.production.frontend"
JAVASCRIPT_IMAGE_TAG := IMAGE_NAME + "-javascript:" + GIT_SHA
JAVASCRIPT_CONTAINER_BUILD_DIR := "/app/build/client"
JAVASCRIPT_PRODUCTION_BUILD_DIR := absolute_path("public")

IMAGE_NAME := PROJECT_NAME
IMAGE_TAG := IMAGE_NAME + ":latest"
PYTHON_BUILD_CMD := "nixpacks build . --name " + IMAGE_NAME + " " + NIXPACKS_BUILD_METADATA

[script]
_production_build_assertions:
	# TODO we should abstract out "IS_CI" to some sort of Justfile check :/

	# only run this on CI
	[ ! -z "${CI:-}" ] || exit 0

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
	nixpacks build {{WEB_DIR}} --name "{{JAVASCRIPT_IMAGE_TAG}}" \
		 {{NIXPACKS_BUILD_METADATA}} \
		--env VITE_BUILD_COMMIT="{{GIT_SHA}}" \
		--build-cmd='pnpm openapi' \
		--start-cmd='pnpm build'

	# we can't just mount /app/build/server with -v since the build process removes the entire /app/build directory
	docker run \
		$(just direnv_export_docker '{{JAVASCRIPT_SECRETS_FILE}}' --params) \
		$(just direnv_export_docker '{{SHARED_ENV_FILE}}' --params) \
		{{JAVASCRIPT_IMAGE_TAG}}

	# container count check is paranioa around https://github.com/orbstack/orbstack/issues/1568. This could cause issues
	# when testing this functionality out locally

	# NOTE watch out for the escaped 'json .' here!
	container_id=$(docker ps --no-trunc -a --format "{{ '{{ json . }}' }}" | jq -r 'select(.Image == "{{JAVASCRIPT_IMAGE_TAG}}") | .ID') && \
		[ "$(echo "$container_id" | wc -l)" -eq 1 ] || (echo "Expected exactly one container, got $container_id" && exit 1) && \
		docker cp $container_id:{{JAVASCRIPT_CONTAINER_BUILD_DIR}} "{{JAVASCRIPT_PRODUCTION_BUILD_DIR}}" && \
		docker rm $container_id

# support non-macos installations for github actions
_build_requirements:
	@if ! which nixpacks > /dev/null; then \
		echo "nixpacks is not installed. Installing...."; \
		{{ if os() == "macos" { "brew install nixpacks" } else { "curl -sSL https://nixpacks.com/install.sh | bash" } }}; \
	fi

# url of the repo on github for build metadata
@_repo_url:
	gh repo view --json url --jq ".url" | tr -d " \n"

# unique ID (mostly) to identify where/when this image was built for docker labeling
@_build_id:
	if [ -z "${GITHUB_RUN_ID:-}" ]; then \
		echo "{{ os() }}-$(whoami)"; \
	else \
		echo "$GITHUB_RUN_ID"; \
	fi

# build the docker container using nixpacks
build: _build_requirements _production_build_assertions build_js-assets
	@echo "Building python application..."
	{{PYTHON_BUILD_CMD}} \
		$(just direnv_export_docker '{{SHARED_ENV_FILE}}' --params) \
		$(just direnv_export_docker '{{PYTHON_PRODUCTION_ENV_FILE}}' --params) \
		--label org.opencontainers.image.revision={{GIT_SHA}} \
		--label org.opencontainers.image.created="{{BUILD_CREATED_AT}}" \
		--label org.opencontainers.image.source="$(just _repo_url)" \
		--label "build.run_id=$(just _build_id)"

# dump json output of the built image, ex: j build_inspect '.Config.Env'
build_inspect *flags:
	docker image inspect --format "{{ '{{ json . }}' }}" "{{IMAGE_TAG}}" | jq -r {{ flags }}

# interactively inspect the layers of the built image
[macos]
build_dive: (_brew_check_and_install "dive")
	dive "{{IMAGE_TAG}}"

# dump nixpacks-generated Dockerfile for manual build and production debugging
build_dump:
	{{PYTHON_BUILD_CMD}} --out .

build_clean:
	rm -rf .nixpacks web/.nixpacks || true

# inject a shell where the build fails
build_debug: build_dump
	# note that you *may* run into trouble using the interactive injected shell if you are using an old builder version
	# Force the latest builder: `docker buildx use orbstack`

	# store the modified build command in a variable rather than editing the file
	BUILD_DEBUG_CMD=$(sed 's/docker build/BUILDX_EXPERIMENTAL=1 docker buildx debug --invoke bash build/' .nixpacks/build.sh) && \
		eval "$BUILD_DEBUG_CMD"

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

	# without clearing the env, any variables that you have set in your shell (via ~/.exports or similar) will *not*
	# be included in the export. This was occuring on my machine since I set PYTHON* vars globally. To work around this
	# we clear the environment, outside of the PATH + HOME required for direnv configuration.
	env -i HOME="$HOME" PATH="$PATH" \
		RENDER_DIRENV="{{target}}" direnv export json 2>/dev/null | jq -r '{{jq_script}}'


# export env variables for a particular file in a format docker can consume
[doc("Export as docker '-e' params: --params")]
@direnv_export_docker target *flag:
	# clear all contents of the tmp dir

	if {{ if flag == "--params" { "true" } else { "false" } }}; then; \
		just direnv_export "{{target}}" | jq -r 'to_entries | map("-e \(.key)=\(.value)") | join(" ")'; \
	else; \
		just direnv_export "{{target}}" | jq -r 'to_entries[] | "\(.key)=\(.value)"'; \
	fi

