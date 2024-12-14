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
# * Make CI more portable. By including as much logic as possible within the Justfile you can
#   easily move to a different CI system if you need to.
# * Be greedy about new scripts that help optimize the devloop environment. Just autocomplete + fzf makes it easy to
#   and sort through really long lists of recipes.
# * Scripts marked as `[macos]` should only run on dev machines. By default, this setup does not support non-macos
#   dev machines.
#
#######################

# _ is currently being used a recipe namespace char, use `-` to separate words
# TODO this will be improved later on: https://github.com/casey/just/issues/2442

# `pipefail` is important: without this option, a shell script can easily hide an error in a way that is hard to debug
# this will cause some extra frustration when developing scripts initially, but will make working with them more
# intuitive and less error prone over time.

# zsh is the default shell under macos, let's mirror it
set shell := ["zsh", "-cu", "-o", "pipefail"]

# TODO v (cmd tracing) by default for [script]? created weird terminal clearing behavior
# TODO can we force tracing and a custom PS4 prompt? Would be good to understand how Just handles echoing commands
# set script-interpreter := ["zsh", "-euvBh"]

# determines what shell to use for [script]
set script-interpreter := ["zsh", "-euBh", "-o", "pipefail"]

# avoid seeing comments in the output
set ignore-comments := true

# for [script] support
set unstable := true

# used for image name, op vault access, etc
PROJECT_NAME := "python-starter-template"

# execute a command in the (nearly) exact same environment as CI
EXECUTE_IN_TEST := "CI=true direnv exec ."

# the `exec` magic is to ensure `sys.stdout.isatty()` reports as false, which can change pytest plugin functionality
# exec 1> >(cat)

default:
	just --list

# start all of the services you need for development in a single terminal
[macos]
[script]
dev: local-alias setup
	# create a tmp Procfile with all of the dev services we need running
	cat << 'EOF' > tmp/Procfile.dev
	py_dev: just py_dev
	js_dev: just js_dev
	js_generate_openapi: just js_generate-openapi --watch
	EOF

	# TODO should we add a watcher for JS and rebuild the static JS build for e2e py tests?

	foreman start --procfile=tmp/Procfile.dev

#######################
# Setup
#######################

# NOTE nixpacks is installed during the deployment step and not as a development prerequisite
BREW_PACKAGES := "fd entr 1password-cli yq jq"
EXTRA_BREW_PACKAGES := "lefthook peterldowns/tap/localias foreman"

[macos]
[script]
_brew_check_and_install brew_target:
	if ! brew list {{brew_target}} > /dev/null; then
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

	@if ! which docker > /dev/null; then \
		echo "docker is not installed. Please install."; \
		exit 1; \
	fi

	@for brew_package in {{BREW_PACKAGES}}; do \
		just _brew_check_and_install $brew_package; \
	done

	@if ! which commitlint > /dev/null; then \
		if ! cargo --list | grep -q binstall; then \
			echo "cargo binstall not available, skipping commitlint installation"; \
		else \
			cargo binstall -y commitlint-rs; \
		fi; \
	fi

	@if [[ "{{flags}}" =~ "--extras" ]]; then \
		echo "Adding aiautocommit..."; \
		uv tool add aiautocommit; \
		echo "Removing sample git hooks..."; \
		rm .git/hooks/*.sample || true; \
		echo "Installing git hooks..."; \
		lefthook install; \
		for brew_package in {{EXTRA_BREW_PACKAGES}}; do \
			just _brew_check_and_install $brew_package; \
		done; \
	fi

# setup everything you need for local development
[macos]
setup: requirements && py_setup db_seed js_build
	# NOTE this task should be non-destructive, the user should opt-in to something like `nuke`

	# some reasoning behind the logic here:
	#
	# 	- js_build is required for running e2e tests on the server

	@if [ ! -f .env.dev.local ]; then \
		cp .env.dev.local-example .env.dev.local; \
		echo "Please edit .env.dev.local to your liking."; \
	fi

	@if [ ! -f .env.local ]; then \
		cp .env.local-example .env.local; \
		echo "Please edit .env.local to your liking."; \
	fi

	@echo 'If you are using localais, run `just local-alias` to start the daemon'

# TODO extract to my personal dotfiles as well
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

	# TODO https://discord.com/channels/1066429325269794907/1314301006992900117/1316773799688933406
	mise install

	just _mise_version_sync
	git add .tool-versions


# sync the mise version to github actions yaml
[macos]
_mise_version_sync:
	mise_version=$(mise --version | awk '{print $1}') && \
		yq e '.runs.steps.0.with.version = "'$mise_version'"' .github/actions/common-setup/action.yml -i

	git add .github/actions/common-setup/action.yml

# upgrade mise, language versions, and essential packages
[macos]
tooling_upgrade: && _mise_upgrade _js_sync-engine-versions
	mise self-update
	HOMEBREW_NO_AUTO_UPDATE=1 brew upgrade {{BREW_PACKAGES}}

# upgrade everything: all packages on all languages, tooling, etc
[macos]
upgrade: tooling_upgrade js_upgrade py_upgrade

# run (or reload) daemon to setup local development aliases
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

# destroy and rebuild py, js, db, etc
nuke: js_nuke py_nuke db_nuke

#######################
# Javascript
#######################

WEB_DIR := "web"
_pnpm := "cd " + WEB_DIR + " && pnpm ${PNPM_GLOBAL_FLAGS:-}"

js_setup:
	{{_pnpm}} install
	# TODO do we actually need this? Or will RR do this for us when building a preview + build?
	{{_pnpm}} react-router typegen

js_clean:
	rm -rf {{WEB_DIR}}/build {{WEB_DIR}}/client {{WEB_DIR}}/node_modules {{WEB_DIR}}/.react-router || true

# clean and rebuild
js_nuke: js_clean js_setup

js_lint +FILES=".":
	# TODO support GITHUB_ACTIONS/CI formatting
	{{_pnpm}} prettier --check {{FILES}}
	# `eslint-config-typescript` seems dead
	{{_pnpm}} eslint --cache --cache-location ./node_modules/.cache/eslint {{FILES}}

	{{_pnpm}} dlx depcheck

# automatically fix linting errors
js_lint-fix:
	{{_pnpm}} prettier --write .
	{{_pnpm}} eslint --cache --cache-location ./node_modules/.cache/eslint . --fix

# run tests in the exact same environment that will be used on CI
js_test:
	# NOTE vitest automatically will detect GITHUB_ACTIONS and change the output format
	# CI=true impacts how various JS tooling run
	if [[ -n "${CI:-}" ]]; then \
		{{_pnpm}} run test; \
	else \
		cd {{WEB_DIR}} && {{EXECUTE_IN_TEST}} pnpm run test; \
	fi

# run a development server
js_dev:
	[[ -d {{WEB_DIR}}/node_modules ]] || just js_setup
	{{_pnpm}} run dev

# build a production javascript bundle, helpful for running e2e python tests
js_build: js_setup
	# as you'd expect, the `web/build` directory is wiped on each run, so we don't need to clear it manually
	export VITE_BUILD_COMMIT="{{GIT_SHA}}" && {{_pnpm}} run build

# interactive repl for testing ts
js_play:
	# TODO this needs some work
	{{_pnpm}} dlx tsx ./playground.ts

# interactively upgrade all js packages
js_upgrade:
	{{_pnpm}} dlx npm-check-updates --interactive
	{{_pnpm}} install
	cd {{WEB_DIR}} && git add package.json pnpm-lock.yaml

# generate a typescript client from the openapi spec
[doc("Optional flag: --watch")]
js_generate-openapi *flag:
	if {{ if flag == "--watch" { "true" } else { "false" } }}; then; \
		fd --extension=py . | entr just _js_generate-openapi; \
	else; \
		just _js_generate-openapi; \
	fi

_js_generate-openapi:
	# jq is here to pretty print the output
	LOG_LEVEL=error uv run python -m app.server | jq -r . > "$OPENAPI_JSON_PATH"

	# generate the js client with the latest openapi spec
	{{_pnpm}} run openapi

# run shadcn commands with the latest library version
js_shadcn *arguments:
	{{_pnpm}} dlx shadcn@latest {{arguments}}

JAVASCRIPT_PACKAGE_JSON := WEB_DIR / "package.json"

# update package.json engines to match the current versions in .tool-versions
[macos]
[script]
_js_sync-engine-versions:
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

# this is used for jinja + HTML linting, if you put templates elsewhere, you'll need to update this
JINJA_TEMPLATE_DIR := "app/templates"

# create venv and install packages
py_setup:
	[ -d ".venv" ] || uv venv

	# don't include debugging-extras on CI
	# --no-sources to allow local dev packages to be used: https://github.com/astral-sh/uv/issues/9258#issuecomment-2499541207
	if [ -z "${CI:-}" ]; then \
		uv sync --group=debugging-extras; \
	else \
		uv sync --no-sources; \
	fi

	# important for CI to install browsers for playwright
	# the installation process is fast enough (<10s) to eliminate the need for attempting to cache via GHA
	# if this turns out not to be true, we should implement: https://github.com/hirasso/thumbhash-custom-element/blob/main/.github/workflows/tests.yml

	if [ -z "${CI:-}" ]; then \
		uv run playwright install chromium; \
	else \
		uv run playwright install chromium --only-shell; \
	fi

# clean entire py project without rebuilding
py_clean:
	# pycache should never appear because of PYTHON* vars

	rm -rf .pytest_cache .ruff_cache .venv celerybeat-schedule
	rm -rf tests/**/snapshot_tests_failures
	# rm -rf $PLAYWRIGHT_BROWSERS_PATH


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
	uv run fastapi dev --port $PYTHON_SERVER_PORT

py_play:
	./playground.py

# TODO should have additional tool for workers and all server processes

# run all linting operations and fail if any fail
[script]
py_lint +FILES=".":
	# + indicates one more arguments being required in Justfile syntax

	# NOTE this is important: we want all operations to run instead of fail fast
	set +e

	# Define a more detailed colored PS4 without current directory so -x output is easier to read
	setopt prompt_subst
	export PS4='%F{green}+%f '
	set -x

	if [ -n "${CI:-}" ]; then
		# TODO I'm surprised that ruff doesn't auto detect github...
		uv tool run ruff check --output-format=github {{FILES}} || exit_code=$?

		uv run pyright {{FILES}} --outputjson > pyright_report.json || exit_code=$?
		# TODO this is a neat trick, we should use it in other places too + document
		# https://docs.github.com/en/actions/writing-workflows/choosing-what-your-workflow-does/workflow-commands-for-github-actions#setting-a-warning-message
		# https://github.com/jakebailey/pyright-action/blob/b7d7f8e5e5f195796c6f3f0b471a761a115d3b2c/src/main.ts#L62
		jq -r '.generalDiagnostics[] | "::\(.severity) file=\(.file),line=\(.range.start.line),endLine=\(.range.end.line),col=\(.range.start.character),endColumn=\(.range.end.character)::\(.message)"' < pyright_report.json
		rm pyright_report.json

		# check jinja2 template language
		uv run j2lint --extension j2,html {{JINJA_TEMPLATE_DIR}} --json > j2link_report.json || exit_code=$?
		jq -r '(.ERRORS[] | "::\(if .severity == "HIGH" then "error" else "warning" end) file=\(.filename),line=\(.line_number),title=\(.id)::\(.message)"), (.WARNINGS[] | "::warning file=\(.filename),line=\(.line_number),title=\(.id)::\(.message)")' < j2link_report.json
		rm j2link_report.json
	else
		uv tool run ruff check {{FILES}} || exit_code=$?
		uv run pyright {{FILES}} || exit_code=$?
		uv run j2lint --extension j2,html {{JINJA_TEMPLATE_DIR}}
	fi

	# TODO should only run if {{FILES}} contains a template
	# NOTE djlint does *not* check jinja syntax, only HTML. GH friendly output is automatically enabled.
	uv run djlint {{JINJA_TEMPLATE_DIR}} --profile=jinja

	# TODO right now, this tool doesn't work with manual maps :/
	# TODO https://github.com/fpgmaas/deptry/issues/610#issue-2190147786
	# TODO https://github.com/fpgmaas/deptry/issues/740
	# uv tool run deptry --experimental-namespace-package . || exit_code=$?

	if [[ -n "${exit_code:-}" ]]; then
		echo "One or more commands failed"
		exit 1
	fi

# automatically fix linting errors
py_lint_fix:
	uv tool run ruff check . --fix
	uv run djlint --profile=jinja --reformat {{JINJA_TEMPLATE_DIR}}

	# NOTE pyright and other linters do not have an automatic fix flow

# build js for py e2e tests
py_js-build:
	# integration tests should mimic production as closely as possible
	# to do this, we build the app and serve it like it will be served in production
	export PNPM_GLOBAL_FLAGS="--silent" && {{EXECUTE_IN_TEST}} just js_build

PYTEST_COV_PARAMS := "--cov --cov-report=html:${TEST_RESULTS_DIRECTORY}/htmlcov --cov-report=term"

# run tests with the exact same environment that will be used on CI
[script]
py_test: py_js-build
	# Define a more detailed colored PS4 without current directory so -x output is easier to read
	setopt prompt_subst
	export PS4='%F{green}+%f '
	set -x

	# TODO we don't need to see all of the details for this part of the build, since we are primarily testing javascript

	# TODO I wonder if I could make EXECUTE_IN_TEST blank if in the test environment...
	# NOTE unfortunately, because of the asyncio loop + playwright, we need to run the playwright integration tests separately
	if [[ -n "${CI:-}" ]]; then
		uv run pytest . --ignore tests/integration {{PYTEST_COV_PARAMS}}
		uv run pytest tests/integration --cov-append {{PYTEST_COV_PARAMS}}
	else
		{{EXECUTE_IN_TEST}} uv run pytest . --ignore tests/integration {{PYTEST_COV_PARAMS}}
		{{EXECUTE_IN_TEST}} uv run pytest tests/integration --cov-append {{PYTEST_COV_PARAMS}}
	fi

# open playwright trace viewer on last trace zip. --remote to download last failed remote trace
[macos]
py_playwright_trace remote="":
		# helpful to download to unique folder for two reasons: (a) easier to match up to web GHA view and (b) eliminates risk of gh-cli erroring out bc the directory already exists
		if [ "{{remote}}" = "--remote" ]; then \
				failed_run_id=$(just _gha_last_failed_run_id) && \
				mkdir -p ${PLAYWRIGHT_RESULT_DIRECTORY}/${failed_run_id} && \
				gh run --dir ${PLAYWRIGHT_RESULT_DIRECTORY}/${failed_run_id} download $failed_run_id; \
		fi

		# NOTE it's insane, but fd does not have a "find last modified file"
		# https://github.com/sharkdp/fd/issues/196
		uv run playwright show-trace $(fd --no-ignore-vcs . ${PLAYWRIGHT_RESULT_DIRECTORY} -e zip -t f --exec-batch stat -f '%m %N' | sort -n | tail -1 | cut -f2- -d" ")

# record playwright interactions for integration tests and dump them to a file
[macos]
[script]
py_playwright:
	mkdir -p tmp/playwright
	recorded_interaction=tmp/playwright/$(date +%m-%d-%s).py

	uv run playwright codegen --target python-pytest --output $recorded_interaction https://${JAVASCRIPT_SERVER_HOST}

	echo $recorded_interaction
	pbcopy < $recorded_interaction

# open mailpit web ui, helpful for inspecting emails
py_mailpit_open:
	open "https://$(echo $SMTP_URL | cut -d'/' -f3 | cut -d':' -f1)"

#######################
# CI Management
#######################

GHA_YML_NAME := "build_and_publish.yml"

# TODO should scope to the current users runs
# rerun last failed CI run
ci_rerun:
	gh run rerun $(just _gha_last_failed_run_id)

# view the last failed gha in the browser
ci_view-last-failed:
	gh run view --web $(just _gha_last_failed_run_id)

# TODO output here is still messy, may be able to customize with --template
# tail failed logs right in your terminal
ci_tail-last-failed:
	gh run view --log-failed $(just _gha_last_failed_run_id)

# live tail currently running ci job
ci_watch-running *flag:
	if {{ if flag == "--web" { "true" } else { "false" } }}; then \
		gh run view --web $(just _gha_running_run_id); \
	else \
		gh run watch $(just _gha_running_run_id); \
	fi

# very destructive action: deletes all workflow run logs
[confirm('Are you sure you want to delete all workflow logs?')]
ci_wipe_run_logs:
	REPO=$(gh repo view --json name --jq '.name') && \
	OWNER=$(gh repo view --json owner --jq '.owner.login') && \
		gh api repos/$OWNER/$REPO/actions/workflows --paginate --jq '.workflows[] | .id' | \
		xargs -I{} gh api repos/$OWNER/$REPO/actions/workflows/{}/runs --paginate --jq '.workflow_runs[].id' | \
			xargs -I{} gh api -X DELETE /repos/$OWNER/$REPO/actions/runs/{}

# get the last failed run ID
_gha_last_failed_run_id:
	# NOTE this is tied to the name of the yml!
	gh run list --status=failure --workflow={{GHA_YML_NAME}} --json databaseId --jq '.[0].databaseId'

_gha_running_run_id:
	gh run list --status=in_progress --workflow={{GHA_YML_NAME}} --json databaseId --jq '.[0].databaseId'

#######################
# Dev Container Management
#######################

# Use --fast to avoid waiting until the containers are healthy, useful for CI runs
[doc("Optional flag: --fast")]
up *flag:
	docker compose up -d {{ if flag == "--fast" { "" } else { "--wait" } }}

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
db_reset: db_down db_up db_migrate

db_lint:
	uv run alembic check

	# TODO there's also a more advanced github integration, but seems a bit cleaner:
	# https://squawkhq.com/docs/github_app

	# TODO don't fail on warnings https://github.com/sbdchd/squawk/issues/348
	# TODO remove rule exclusion when https://github.com/sbdchd/squawk/issues/392 is fixed
	# TODO should submit upstream for the jq transformations so others can copy, add to docs
	if [ -n "${CI:-}" ]; then \
		LOG_LEVEL=error uv run alembic upgrade head --sql | \
			uv run squawk --reporter=json --exclude=prefer-text-field | \
			jq -r '.[] | "::\(if .level == "Error" then "error" else "warning" end) file=\(.file),line=\(.line),col=\(.column),title=\(.rule_name)::\(.messages[0].Note)"'; \
	else \
		LOG_LEVEL=error uv run alembic upgrade head --sql | uv run squawk --exclude=prefer-text-field; \
	fi

# open the database in the default macos GUI
[macos]
db_open:
	# TablePlus via Setapp is a great option here
	open $DATABASE_URL

# tui to interact with the database
[macos]
db_play:
	uv tool run pgcli $DATABASE_URL

# migrations on dev and test
db_migrate:
	# dev database is created automatically, but test database is not. We need to fail gracefully when the database already exists.
	psql $DATABASE_URL -c "CREATE DATABASE ${TEST_DATABASE_NAME};" || true

	uv run alembic upgrade head

	[ -n "${CI:-}" ] || {{EXECUTE_IN_TEST}} uv run alembic upgrade head

# add seed data to dev and test
db_seed: db_migrate
	uv run python migrations/seed.py
	[ -n "${CI:-}" ] || {{EXECUTE_IN_TEST}} uv run python migrations/seed.py

# generate migration based on the current state of the database
[script]
db_generate_migration migration_name="":
	if [ -z "{{migration_name}}" ]; then
		echo "Enter the migration name (use add/remove/update prefix): "
		read name
	else
		name={{migration_name}}
	fi

	# underscores & alpha chars only
	name=$(echo "$name" | tr ' ' '_' | tr '-' '_' | tr -cd '[:alnum:]_')

	uv run alembic revision --autogenerate -m "$name"

# destroy and rebuild the database from the ground up, without mutating migrations
db_destroy: db_reset db_migrate db_seed

# destroy all migrations and rebuild everything: only for use in early development
db_nuke: db_reset && db_migrate db_seed
	# I personally hate having a nearly-greenfield project with a bunch of migrations from DB schema iteration
	# this should only be used *before* you've launched and prod and don't need properly migration support
	rm -rf migrations/versions/* || true
	just db_generate_migration "initial_commit"

# enable SQL debugging on the postgres database
[macos]
db_debug:
	docker compose exec postgres \
		psql -U $POSTGRES_USER -c "ALTER SYSTEM SET log_statement = 'all'; SELECT pg_reload_conf();"

[macos]
db_debug_off:
	docker compose exec postgres \
		psql -U $POSTGRES_USER -c "ALTER SYSTEM SET log_statement = 'none'; SELECT pg_reload_conf();"

#######################
# Secrets
#######################

_secrets_service-token CONTEXT:
	# if OP_SERVICE_ACCOUNT_TOKEN is set, the service-account API will not work
	unset OP_SERVICE_ACCOUNT_TOKEN && \
	op service-account create {{PROJECT_NAME}}-{{CONTEXT}} \
			--expires-in '90d' \
			--vault "${OP_VAULT_UID}:read_items" \
			--raw

# generate service account token to be used locally for a developer
[macos]
secrets_local-service-token user=`whoami`:
	just _secrets_service-token {{user}} | jq -r -R '@sh "export OP_SERVICE_ACCOUNT_TOKEN=\(.)"'

# grant GH actions access to the 1p vault, this needs to be done every 90d
[macos]
secrets_ci_grant-github-actions:
	# 90d is the max expiration time allowed
	# this can be safely run multiple times, it will not regenerate the service account token
	service_account_token=$(just _secrets_service-token github-actions) && \
		gh secret set OP_SERVICE_ACCOUNT_TOKEN --app actions --body "$service_account_token"

# manage the op service account from the web ui
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

# TODO fly deployment and other options, this needs some work

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

# NOTE production secrets are *not* included in the image, they are set on deploy
PYTHON_NIXPACKS_BUILD_CMD := "nixpacks build ." + \
	" --name " + PYTHON_IMAGE_TAG + \
	" " + NIXPACKS_BUILD_METADATA + \
	" $(just direnv_export_docker '" + SHARED_ENV_FILE +"' --params)" + \
	" --inline-cache --cache-from " + PYTHON_PRODUCTION_IMAGE_NAME + ":latest" + \
	" --label org.opencontainers.image.revision='" + GIT_SHA + "'" + \
	" --label org.opencontainers.image.created='" + BUILD_CREATED_AT + "'" + \
	' --label org.opencontainers.image.source="$(just _repo_url)"' + \
	' --label org.opencontainers.image.description="Primary application deployment image"' + \
	' --label build.run_id="$(just _build_id)"'

# .env file without any secrets that should exist on all environments
SHARED_ENV_FILE := ".env"

# .env file with production variables, no secrets, for python
PYTHON_PRODUCTION_ENV_FILE := ".env.production.backend"

# .env file with production variables that are safe to share publicly (frontend)
JAVASCRIPT_SECRETS_FILE := ".env.production.frontend"

# by default, the py image name is pulled from the project name
PYTHON_IMAGE_NAME := PROJECT_NAME
PYTHON_IMAGE_TAG := PYTHON_IMAGE_NAME + ":" + GIT_SHA

# the js image is not deployed and is only used during build, so we simply add a -javascript suffix
JAVASCRIPT_IMAGE_NAME := PYTHON_IMAGE_NAME + "-javascript"
JAVASCRIPT_IMAGE_TAG := JAVASCRIPT_IMAGE_NAME + ":" + GIT_SHA

PYTHON_PRODUCTION_IMAGE_NAME := "ghcr.io/iloveitaly/python-starter-template"
JAVASCRIPT_PRODUCTION_IMAGE_NAME := PYTHON_PRODUCTION_IMAGE_NAME + "-javascript"

[script]
_production_build_assertions:
	# TODO we should abstract out "IS_CI" to some sort of Justfile check :/

	# only run this on CI
	[ ! -z "${CI:-}" ] || exit 0

	# if the workspace is dirty, some configuration is not correct: we want a completely clean build environment
	if [ ! -z "{{GIT_DIRTY}}" ]; then \
			echo "Git workspace is dirty! This should never happen on prod!" >&2; \
			git status; \
			exit 1; \
	fi

	if [ ! -d "{{JINJA_TEMPLATE_DIR}}" ]; then \
		echo "Jinja template directory does not exist! This should never happen on prod" >&2; \
		exit 1; \
	fi

# within nixpacks, this is where the SPA client assets are built
JAVASCRIPT_CONTAINER_BUILD_DIR := "/app/build/client"
# outside of nixpacks, within the python application folder, this is where the SPA assets are stored
JAVASCRIPT_PRODUCTION_BUILD_DIR := "public"

# build the javascript assets by creating an image, building assets inside the container, and then copying them to the host
build_js-assets: _production_build_assertions
	@echo "Building javascript assets..."
	rm -rf "{{JAVASCRIPT_PRODUCTION_BUILD_DIR}}" || true

	# Production assets bundle public "secrets" (safe to expose publicly) which are extracted from the environment
	# for this reason, we need to emulate the production environment, then build the assets statically.
	# Also, we can't just mount /app/build/server with -v since the build process removes the entire /app/build directory
	nixpacks build {{WEB_DIR}} \
		--name "{{JAVASCRIPT_IMAGE_TAG}}" \
		 {{NIXPACKS_BUILD_METADATA}} \
		--env VITE_BUILD_COMMIT="{{GIT_SHA}}" \
		--cache-from "{{JAVASCRIPT_PRODUCTION_IMAGE_NAME}}:latest" --inline-cache \
		$(just direnv_export_docker '{{JAVASCRIPT_SECRETS_FILE}}' --params) \
		$(just direnv_export_docker '{{SHARED_ENV_FILE}}' --params) \
		--label org.opencontainers.image.description="Used for building javascript assets, not for deployment" \

	# you cannot extract files out of a image, only a container
	docker rm tmp-js-container || true
	docker create --name tmp-js-container {{JAVASCRIPT_IMAGE_TAG}}
	docker cp tmp-js-container:/app/build/production/client "{{JAVASCRIPT_PRODUCTION_BUILD_DIR}}"

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
	{{PYTHON_NIXPACKS_BUILD_CMD}}

build_push: _production_build_assertions
	# JS image is not used in prod, but is used for nixpacks caching, so we push to the registry
	docker tag {{PYTHON_IMAGE_TAG}} {{PYTHON_PRODUCTION_IMAGE_NAME}}:{{GIT_SHA}}
	docker push {{PYTHON_PRODUCTION_IMAGE_NAME}}:{{GIT_SHA}}

	docker tag {{PYTHON_IMAGE_TAG}} {{PYTHON_PRODUCTION_IMAGE_NAME}}:latest
	docker push {{PYTHON_PRODUCTION_IMAGE_NAME}}:latest

	docker tag {{JAVASCRIPT_IMAGE_TAG}} {{JAVASCRIPT_PRODUCTION_IMAGE_NAME}}:latest
	docker push {{JAVASCRIPT_PRODUCTION_IMAGE_NAME}}:latest

# dump json output of the built image, ex: j build_inspect '.Config.Env'
build_inspect *flags:
	docker image inspect --format "{{ '{{ json . }}' }}" "{{PYTHON_IMAGE_TAG}}" | jq -r {{ flags }}

# interactively inspect the layers of the built image
[macos]
build_dive: (_brew_check_and_install "dive")
	dive "{{PYTHON_IMAGE_TAG}}"

# dump nixpacks-generated Dockerfile for manual build and production debugging
build_dump:
	{{PYTHON_NIXPACKS_BUILD_CMD}} --out .

# clear out nixpacks and other artifacts specific to production containers
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
	docker run -it {{PYTHON_IMAGE_TAG}} bash -l

# open up a *second* shell in the *same* container that's already running
build_shell-exec:
	docker exec -it $(docker ps -q --filter "ancestor={{PYTHON_IMAGE_TAG}}") bash -l

# run the container locally, as if it were in production (against production DB, resources, etc)
[script]
build_run-as-production procname="":
	# NOTE that resources are limited to a production-like environment, change if your production requirements are different
	docker run -p 8202:80 \
		--memory=1g --cpus=2 \
		$(just direnv_export_docker "" --params) \
		"{{PYTHON_IMAGE_TAG}}" \
		"$(just extract_proc "{{procname}}")"

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
		(.key | startswith("DIRENV_") | not)
		and (.key | startswith("OP_") | not)
		and (.key | IN("VIRTUAL_ENV", "VENV_ACTIVE", "UV_ACTIVE", "PATH") | not)
	))
)
"""

# TODO report this upstream to direnv, this is an insane workaround :/
# target a specific .env file (supports direnv features!) for export as a JSON blob
@direnv_export target="":
	([ ! -n "{{target}}" ] || [ -f "{{target}}" ]) || (echo "{{target}} does not exist"; exit 1)
	[ "{{target}}" != ".envrc" ] || (echo "You cannot use .envrc as a target"; exit 1)

	# without a clear env (env -i), any variables set in your shell (via ~/.exports or similar) will *not* be included
	# in `direnv export`. I originally discovered this because PYTHON* vars were not being exported because they were set
	# globally. To work around this we clear the environment, outside of the PATH + HOME required for direnv configuration.
	# OP_SERVICE_ACCOUNT_TOKEN is also included since on CI this is effectively global state that enables 1p access.
	# When run on your local machine, 1p global state may be persisted elsewhere, so this would be a noop.
	env -i HOME="$HOME" PATH="$PATH" OP_SERVICE_ACCOUNT_TOKEN="${OP_SERVICE_ACCOUNT_TOKEN:-}" op daemon -d
	env -i HOME="$HOME" PATH="$PATH" OP_SERVICE_ACCOUNT_TOKEN="${OP_SERVICE_ACCOUNT_TOKEN:-}" \
		RENDER_DIRENV="{{target}}" \
		direnv export json | jq -r '{{jq_script}}'

	# TODO the `op daemon -d` hack above is to workaround a op bug:
	# https://1password-devs.slack.com/archives/C03NJV34SSC/p1733771530356779

# export env variables for a particular file in a format docker can consume
[doc("Export as docker '-e' params: --params\nExport as shell: --shell")]
@direnv_export_docker target *flag:
	# NOTE @sh below does NOT handle newlines, tabs, etc in ANSI-C format like direnv does
	#      https://github.com/iloveitaly/direnv/blob/1a39d968c165fddff3b9a4c5538025d71f73ee43/internal/cmd/shell_bash.go#L97
	#      this could cause issues for us, although it seems as though @sh just includes the literal newline or tab char
	# 		 instead of the escaped version, which is most likely fine.

	if {{ if flag == "--params" { "true" } else { "false" } }}; then; \
		just direnv_export "{{target}}" | jq -r 'to_entries | map("-e \(.key)=\(.value)") | join(" ")'; \
	elif {{ if flag == "--shell" { "true" } else { "false" } }}; then; \
	  just direnv_export "{{target}}" | jq -r 'to_entries[] | "export \(.key)=\(.value | @sh)"'; \
	else; \
		just direnv_export "{{target}}" | jq -r 'to_entries[] | "\(.key)=\(.value)"'; \
	fi

	# last case is exporting as a docker file (i.e. no export)
	# TODO note this is not currently in use, so we'll probably have to tweak it in the future

BASH_EXPORT_PREAMBLE := """
export PATH="$HOME/.local/bin:$PATH"

eval "$(mise activate)"
eval "$(just --completions $(basename $SHELL))"

## BEGIN DIRENV EXPORT
"""

# export direnv variables as a bash script to avoid using direnv and mutating your environment configuration
[macos]
[script]
direnv_bash_export:
	target_file=".env.$(whoami).local"

	echo '{{BASH_EXPORT_PREAMBLE}}' > "$target_file"
	just direnv_export_docker "" --shell >> "$target_file"

	echo $'\n'
	echo "File generated: $target_file"
	echo "Source using 'source $target_file'"
