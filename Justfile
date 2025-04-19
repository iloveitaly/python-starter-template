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

lint: js_lint py_lint db_lint

# watches all important python files and automatically restarts the process if anything changes
PYTHON_WATCHMEDO := "uv run --with watchdog watchmedo auto-restart --directory=./ --pattern=*.py --recursive --"

# start all of the services you need for development in a single terminal
[macos]
[script]
dev: local-alias dev_kill
	just _banner_echo "Starting dev services"

	# TODO we should think about the worker command a bit more...should we use the same exact command? should we generate vs hardcode?
	# create a tmp Procfile with all of the dev services we need running
	cat << 'EOF' > tmp/Procfile.dev
	py_dev: just py_dev
	py_worker: {{PYTHON_WATCHMEDO}} $(yq '.worker' Procfile --output-format yaml)
	py_scheduler: {{PYTHON_WATCHMEDO}} $(yq '.scheduler' Procfile --output-format yaml)
	js_dev: just js_dev
	openapi: just js_generate-openapi --watch
	EOF

	# foreman is abandonded, but it still works
	# hivemind does not ignore terminal clear control sequences
	# ultraman looks to have some obvious bugs
	foreman start --root . --procfile=tmp/Procfile.dev

# kill all processes bound to server ports
[macos]
[script]
dev_kill:
	just _banner_echo "Killing all processes bound to server ports"

	for port in "$JAVASCRIPT_SERVER_PORT" "$PYTHON_SERVER_PORT" "$PYTHON_TEST_SERVER_PORT"; do
		echo "Checking for processes on port $port"
		pids=("${(@f)$(lsof -t -i :${port} 2>/dev/null || true)}")
		if [[ -n "$pids" ]]; then
			for pid in $pids; do
				kill -9 "$pid"
				echo "Killed process $pid on port $port"
			done
		else
			echo "No processes found on port $port"
		fi
	done

#######################
# Utilities
#######################

# build commands generate a lot of output and when `[script]` is used no commands are echo'd, this lets us make build
# output easier to read in CI.
@_banner_echo BANNER:
	# TODO use style tags from justfile
	# TODO I wonder if sending an endgroup when one isn't started will cause issues.
	([[ -n "${CI:-}" ]] && echo "::endgroup::") || true
	([[ -n "${CI:-}" ]] && echo "::group::{{BANNER}}") || true
	# two spaces added because of the '# ' prefix on the banner message
	banner_length=$(echo -n "{{BANNER}}  " | wc -c) && \
	printf "\n\033[0;36m%${banner_length}s#\033[0m\n" | tr " " "#" && \
	printf "\033[0;36m# %s   \033[0m\n" "{{BANNER}}" && \
	printf "\033[0;36m%${banner_length}s#\033[0m\n\n" | tr " " "#"

#######################
# Setup
#######################

# NOTE nixpacks is installed during the deployment step and not as a development prerequisite
BREW_PACKAGES := "fd entr 1password-cli yq jq fzf"
EXTRA_BREW_PACKAGES := "lefthook peterldowns/tap/localias foreman pstree"

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

	@if [[ "{{flags}}" =~ "--extras" ]]; then \
		echo "Adding aiautocommit..."; \
		uv tool add aiautocommit; \
		\
		echo "Removing sample git hooks..."; \
		rm .git/hooks/*.sample || true; \
		\
		echo "Installing git hooks..."; \
		lefthook install; \
		\
		for brew_package in {{EXTRA_BREW_PACKAGES}}; do \
			just _brew_check_and_install $brew_package; \
		done; \
		\
		if ! which commitlint > /dev/null; then \
			if ! cargo --list | grep -q binstall; then \
				echo "cargo binstall not available, skipping commitlint installation"; \
			else \
				cargo binstall -y commitlint-rs; \
			fi; \
		fi; \
	fi

# setup everything you need for local development
[macos]
setup: requirements && py_setup up db_seed js_build
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

			if [[ "$TOOL" == "node" || "$TOOL" == "python" ]]; then
					# Extract major.minor version
					CURRENT_BASE=$(echo "$CURRENT" | cut -d. -f1,2)
					echo "Current base version of $TOOL: $CURRENT_BASE"

					# Get latest version matching current major.minor
					LATEST=$(mise ls-remote "$TOOL" | grep -E "^${CURRENT_BASE}\.[0-9]+$" | sort -V | tail -n1)
			else
					# Extract major version
					CURRENT_BASE=$(echo "$CURRENT" | cut -d. -f1)
					echo "Current base version of $TOOL: $CURRENT_BASE"

					# Get latest version matching current major version
					LATEST=$(mise ls-remote "$TOOL" | grep -E "^${CURRENT_BASE}\.[0-9.]+$" | sort -V | tail -n1)
			fi

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
	uv run python -m app.cli write-versions
	git add .service-versions

# run (or reload) daemon to setup local development aliases
[macos]
[script]
local-alias:
	if [[ "$(localias status)" == "daemon running with pid "* ]]; then
		just _banner_echo "Localias Daemon Already Running, Reloading"
		localias reload
		exit 0
	fi

	localias start

	just _banner_echo "Local Alias Configuration"

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

# pnpm alias
pnpm +PNPM_CMD:
	{{_pnpm}} {{PNPM_CMD}}

js_setup:
	# frozen-lockfile is used on CI and when building for production, so we default so that mode
	{{_pnpm}} install --frozen-lockfile
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
	# if the server doesn't quit perfectly, it can still consume the port, let's avoid having to think about that
	kill -9 $(lsof -t -i :${JAVASCRIPT_SERVER_PORT}) 2>/dev/null || true
	{{_pnpm}} run dev

# build a production javascript bundle, helpful for running e2e python tests
js_build: js_setup
	# NOTE this is *slightly* different than the production build: NODE_ENV != production and the ENV variables are different
	#      this can cause build errors to occur via nixpacks, but not here.
	#
	# 		 If you want to replicate a production environment, run: `just js_clean && export NODE_ENV=production && just js_build`
	#      to test building in an environment much closer to production. Node and pnpm versions can still be *slightly* different
	#      than your local environment since `mise` is not used within nixpacks.

	# as you'd expect, the `web/build` directory is wiped on each run, so we don't need to clear it manually
	export VITE_BUILD_COMMIT="{{GIT_SHA}}" && {{_pnpm}} run build

# interactive repl for testing ts
js_play:
	# TODO this needs some work
	{{_pnpm}} dlx tsx ./playground.ts

# interactively upgrade all js packages
js_upgrade:
	{{_pnpm}} dlx npm-check-updates --interactive

	# intentionally without lockfile so it's updated
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
	LOG_LEVEL=error uv run python -m app.cli dump-openapi --app-target internal_api_app \
		| jq -r . > "$OPENAPI_JSON_PATH"

	# generate the js client with the latest openapi spec
	{{_pnpm}} run openapi

	# generated route types can dependend on the openapi spec, so we need to regenerate it
	{{_pnpm}} exec react-router typegen

# TODO watch js files
# react-router typegen
# full build for py e2e tests

# run shadcn commands with the latest library version
js_shadcn *arguments:
	{{_pnpm}} dlx shadcn@latest {{arguments}}

js_shadcn_upgrade:
	just js_shadcn diff

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

	# >= vs ^ or ~ can cause weird compatibility issues such as:
	#   https://community.render.com/t/issue-with-deploy/26570/7
	# Always take a conservative approach with javascript system versions.

	jq "
		. + {
			engines: {
				node: \"^$NODE_VERSION\",
				pnpm: \"^$PNPM_VERSION\"
			}
	}" "{{JAVASCRIPT_PACKAGE_JSON}}" > "$tmp_package"

	mv "$tmp_package" "{{JAVASCRIPT_PACKAGE_JSON}}"

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

##########################
# Dev Container Management
##########################

# Use --fast to avoid waiting until the containers are healthy, useful for CI runs
[doc("Optional flag: --fast")]
up *flag:
	# if images have already been pulled, this ensures the latest versions are pulled so they match with
	# CI or other environments that are pulling fresh versions of the images
	docker compose pull

	docker compose up -d {{ if flag == "--fast" { "" } else { "--wait" } }}

down: db_down
	docker compose down

# separate task for the db to support db_reset
db_up:
	docker compose up -d --wait postgres

# TODO may need to run `docker rm $(docker ps -aq)` as well
# TODO docker down does not exit 1 if it partially failed
# turn off the database *and* completely remove the data
db_down:
	docker compose down --volumes postgres

##############################################
# Database Migrations
#
# Goal is to have similar semantics to rails.
##############################################

# completely destroy the dev and test databases, destroying the containers and rebuilding them
db_reset_hard: db_down db_up db_migrate db_seed

# NOTE migration & seed are intentionally omitted so db_nuke and friends can run
# destroys all data in the dev and test databases, leaves the containers running
db_reset:
	psql $DATABASE_URL -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
	psql $TEST_DATABASE_URL -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

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

# run migrations on dev and test
db_migrate:
	# if this folder is wiped, you'll get a strange error from alembic
	mkdir -p migrations/versions

	# dev database is created automatically, but test database is not. We need to fail gracefully when the database already exists.
	psql $DATABASE_URL -c "CREATE DATABASE ${TEST_DATABASE_NAME};" || true

	@just _banner_echo "Migrating Database"

	uv run alembic upgrade head

	[ -n "${CI:-}" ] || (just _banner_echo "Migrating Test Database" && {{EXECUTE_IN_TEST}} uv run alembic upgrade head)

# pick a migration to downgrade to
[macos]
db_downgrade:
	alembic_target_id=$(uv run alembic history | fzf --delimiter '[->\s,]+' --bind 'enter:become(echo {2})') && \
		just _banner_echo "Downgrading Dev Database..." && \
		uv run alembic downgrade $alembic_target_id && \
		just _banner_echo "Downgrading Test Database..." && \
		{{EXECUTE_IN_TEST}} uv run alembic downgrade $alembic_target_id

# add seed data to dev and test
db_seed: db_migrate
	@just _banner_echo "Seeding Database"
	uv run python migrations/seed.py

	[ -n "${CI:-}" ] || (just _banner_echo "Seeding Test Database" && {{EXECUTE_IN_TEST}} uv run python migrations/seed.py)

# TODO you can't preview what the migration will look like before naming it?
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

	just _banner_echo "Migration Generated. Run 'just db_migrate' to apply the migration"

# destroy and rebuild the database from the ground up, without mutating migrations
db_destroy: db_reset db_migrate db_seed

# rm migrations and regenerate: only for use in early development
db_nuke:
	# I personally hate having a nearly-greenfield project with a bunch of migrations from DB schema iteration
	# this should only be used *before* you've launched and prod and don't need properly migration support

	# first, wipe all of the existing migrations
	rm -rf migrations/versions/* || true

	just db_reset
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

# dump the production database locally, obviously this is a bad idea most of the time
[macos]
[script]
db_dump_production:
	echo "{{ BLUE }}Enter the op:// reference to the production DB (e.g., op://Dev/prod DB/db-connection-string):{{ NORMAL }}"
	read op_ref

	local dump_file="tmp/$(date +%Y-%m-%d)_production.dump"
	echo "Dumping production database..."
	pg_dump $(op read "$op_ref") -F c -f "$dump_file"

	echo "Created file: $dump_file"
	echo "Example restore: \n{{ BLUE }}pg_restore --no-owner --no-privileges --if-exists --clean -d \$DATABASE_URL $dump_file{{ NORMAL }}"


# imported justfiles *can* creates some complexity
import 'just/python.just'
import 'just/secrets.just'
import 'just/build.just'
import 'just/github.just'
import 'just/direnv.just'

# TODO imported justfiles are not namespaced by default!
# import? 'infra/Justfile'
