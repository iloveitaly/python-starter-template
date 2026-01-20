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
set shell := ["zsh", "-ceuB", "-o", "pipefail"]

# determines what shell to use for [script]
# TODO can we force tracing and a custom PS4 prompt? Would be good to understand how Just handles echoing commands
set script-interpreter := ["zsh", "-euB", "-o", "pipefail"]

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
	py_generate: just py_generate --watch
	openapi: just js_generate-openapi --watch
	EOF

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

# syncs the project with the upstream python-starter-template repo.
update_from_upstream_template:
	#   - Skips all javascript updates
	#   - You'll need to manually review conflicts of which there will be many
	uv tool run --with jinja2_shell_extension \
		copier update --trust --skip-tasks --skip-answered \
		--exclude web \
		--exclude migrations/versions/ \
		--exclude pyproject.toml \
		--exclude uv.lock \
		--exclude tests/integration/__snapshots__ \
		--exclude .service-versions \
		--exclude .tool-versions \
		--exclude .localias.yaml \
		--exclude .github/instructions \
		--exclude .github/copilot-instructions.md \
		--exclude .cursor/rules

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
	# in most cases, mise will definitely be installed
	@if ! which mise > /dev/null; then \
		echo "mise is not installed."; \
		echo "  => https://mise.jdx.dev"; \
		exit 1; \
	fi

	@if ! which docker > /dev/null; then \
		echo "docker is not installed. Install either docker or OrbStack:"; \
		echo "  => https://docs.docker.com/get-docker/"; \
		echo "  => https://orbstack.dev"; \
		exit 1; \
	fi

	@for brew_package in {{BREW_PACKAGES}}; do \
		just _brew_check_and_install $brew_package; \
	done

	mise install

	# bonus packages that are just for devprod
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
setup: _dev_only requirements && py_setup up db_seed js_setup
	# NOTE this task should be non-destructive, the user should opt-in to something destructive like `nuke`

	# `.local` variants enable the developer to override configuration options without
	# committing them to the repository.
	@if [ ! -f env/dev.local.sh ]; then \
		cp env/dev.local-example.sh env/dev.local.sh; \
		echo "Edit '{{CYAN}}env/dev.local.sh{{NORMAL}}' to your liking."; \
	fi

	@if [ ! -f env/all.local.sh ]; then \
		cp env/all.local-example.sh env/all.local.sh; \
		echo "Edit '{{CYAN}}env/all.local.sh{{NORMAL}}' to your liking."; \
	fi

	@echo 'If you are using localias, run `{{CYAN}}just local-alias{{NORMAL}}` to start the daemon'

# if a dev is having trouble with their environment, this outputs all the versions + debugging information of core tools which could be causing the problem
setup_debug:
	echo $PATH
	uname -m
	zsh --version
	# mise installs everything else
	mise --version
	just --version
	uv --version
	docker --version
	command -v sw_vers >/dev/null 2>&1 && sw_vers -productVersion || echo "sw_vers not found"
	if command -v op >/dev/null 2>&1; then op --version; fi
	direnv exec . zsh -c 'env'

# TODO This needs to work for multiple MIS or tool version files. We should also try to make this more generic so it works for a MIS or a tool version file.
# TODO extract to my personal dotfiles as well
# TODO should change the CURRENT_BASE for py and other x.x.y upgrades
[script]
_mise_upgrade target_dir="": _dev_only
	if [[ -n "{{target_dir}}" ]]; then
		cd "{{target_dir}}"
	fi

	# Get current tools and versions only from paths within this repo
	TOOLS=("${(@f)$(mise list --current --json | jq -r --arg PWD "$PWD" '
		to_entries
		| map(select((.value[0].source.path // "") | startswith($PWD + "/.tool-versions")))
		| from_entries
		| keys[]
	')}")

	minor_updates_only=("python" "node")

	for TOOL in $TOOLS; do
			CURRENT=$(mise list --current --json | jq -r --arg TOOL "$TOOL" --arg PWD "$PWD" '
				to_entries
				| map(select((.value[0].source.path // "") | startswith($PWD + "/")))
				| from_entries
				| .[$TOOL][0].version
			')
			echo "Current version of $TOOL: $CURRENT"

			# do not automatically update a major version for python
			if (( ${minor_updates_only[(I)$TOOL]} )); then
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
tooling_upgrade: _dev_only && _mise_upgrade (_mise_upgrade WEB_DIR) _js_sync-engine-versions
	mise self-update --yes
	HOMEBREW_NO_AUTO_UPDATE=1 brew upgrade {{BREW_PACKAGES}}

# upgrade everything: all packages on all languages, tooling, etc
upgrade: _dev_only tooling_upgrade js_upgrade py_upgrade
	playwright install
	just py_cli write-versions
	git add .service-versions

# this is currently the default global config path
GLOBAL_LOCALIAS_CONFIG := "~/.config/localias.yaml"

# need `[script]` for early exit
# run (or reload) daemon to setup local development aliases
[script]
local-alias: _dev_only
	# We want to support running multiple concurrent projects with different localias configs
	# to do this, we need to use a global config, instead of simply loading from the project config.
	# This is why we iterate over the local config and use the native `set` to update the global config.
	yq eval 'to_entries | .[] | "localias -c {{GLOBAL_LOCALIAS_CONFIG}} set \"\(.key)\" \"\(.value)\""' .localias.yaml | zsh

	# if localias is already running, the above `set` will automatically reload localias with the new aliases
	if [[ "$(localias status)" == "daemon running with pid "* ]]; then
		just _banner_echo "Localias Daemon Already Running, Updated Aliases"
		exit 0
	fi

	localias -c {{GLOBAL_LOCALIAS_CONFIG}} start

	just _banner_echo "Global Local Alias Configuration"
	localias -c {{GLOBAL_LOCALIAS_CONFIG}} debug config --print

clean: js_clean py_clean build_clean
	rm -rf $TMP_DIRECTORY/* || true
	mkdir -p $TMP_DIRECTORY
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
import 'just/dev.just'
