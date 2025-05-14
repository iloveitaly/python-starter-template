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

# zsh is the default shell under macos, let's mirror it everywhere
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


default:
	just --list

lint: js_lint py_lint db_lint

# watches all important python files and automatically restarts the worker process if anything changes
# this is done automatically for fastapi, but not for celery workers
PYTHON_WATCHMEDO := "uv run --with watchdog watchmedo auto-restart --directory=./ --pattern=*.py --recursive --"

# TODO should add an option to not run workers, this is overkill most of the time
# start all of the services you need for development in a single terminal
[script]
dev: _dev_only local-alias dev_kill
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
[script]
dev_kill: _dev_only
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
# Setup
#######################

# NOTE nixpacks is installed during the deployment step and not as a development prerequisite
BREW_PACKAGES := "fd entr 1password-cli yq jq fzf"
EXTRA_BREW_PACKAGES := "lefthook peterldowns/tap/localias foreman pstree"

[script]
_brew_check_and_install brew_target: _dev_only
	if ! brew list {{brew_target}} > /dev/null; then
		echo "{{brew_target}} is not installed. Installing..."
		brew install {{brew_target}}
	fi

# include all development requirements not handled by `mise` for local development
[doc("--extras to install non-essential productivity tooling")]
requirements *flags: _dev_only
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

# setup everything required for local development
setup: _dev_only requirements && py_setup up db_seed js_build
	# NOTE this task should be non-destructive, the user should opt-in to something destructive like `nuke`

	# `.local` variants enable the developer to override configuration options without
	# committing them to the repository.
	@if [ ! -f .env.dev.local ]; then \
		cp .env.dev.local-example .env.dev.local; \
		echo "Edit '.env.dev.local' to your liking."; \
	fi

	@if [ ! -f .env.local ]; then \
		cp .env.local-example .env.local; \
		echo "Edit '.env.local' to your liking."; \
	fi

	@echo 'If you are using localais, run `just local-alias` to start the daemon'

# TODO extract to my personal dotfiles as well
# TODO should change the CURRENT_BASE for py and other x.x.y upgrades
[script]
_mise_upgrade: _dev_only
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
_mise_version_sync: _dev_only
	mise_version=$(mise --version | awk '{print $1}') && \
		yq e '.runs.steps.0.with.version = "'$mise_version'"' .github/actions/common-setup/action.yml -i

	git add .github/actions/common-setup/action.yml

# upgrade mise, language versions, and essential packages
tooling_upgrade: _dev_only && _mise_upgrade _js_sync-engine-versions
	mise self-update
	HOMEBREW_NO_AUTO_UPDATE=1 brew upgrade {{BREW_PACKAGES}}

# upgrade everything: all packages on all languages, tooling, etc
upgrade: _dev_only tooling_upgrade js_upgrade py_upgrade
	uv run python -m app.cli write-versions
	git add .service-versions

# run (or reload) daemon to setup local development aliases
[script]
local-alias: _dev_only
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

# do NOT allow for duplicate recipe names and variables otherwise this would get very complex
import 'just/utils.just'
import 'just/database.just'
import 'just/docker.just'
import 'just/javascript.just'
import 'just/ci.just'
import 'just/python.just'
import 'just/secrets.just'
import 'just/build.just'
import 'just/github.just'
import 'just/direnv.just'
