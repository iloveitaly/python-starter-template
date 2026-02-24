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
# * _ is currently being used a recipe namespace char, use `-` to separate words
#   this will be improved later on: https://github.com/casey/just/issues/2442
# * `pipefail` is important: without this option, a shell script can easily hide an error in a way that is hard to debug
#   this will cause some extra frustration when developing scripts initially, but will make working with them more
#   intuitive and less error prone over time.
# * do NOT allow for duplicate recipe names and variables otherwise this would get very complex
#
#######################

# zsh is the default shell under macos, let's mirror it everywhere
set shell := ["zsh", "-ceuB", "-o", "pipefail"]

# TODO can we force tracing and a custom PS4 prompt? Would be good to understand how Just handles echoing commands
# determines what shell to use for [script]
set script-interpreter := ["zsh", "-euB", "-o", "pipefail"]

# avoid seeing comments in the output
set ignore-comments := true

# for [script] support
set unstable := true

# used for image name, op vault access, etc
PROJECT_NAME := "python-starter-template"

# execute a command in the (nearly) exact same environment as CI
EXECUTE_IN_TEST := "CI=true direnv exec ."

default_message := """
Importand commands:

- setup and setup_debug
- dev and dev_generate
- {py,js}_{clean,test,lint,lint_fix,dev,generate}
"""

default:
		@echo "{{ default_message }}"

# run automatic fix operations for all linters
[parallel]
fix: js_lint-fix py_lint_fix

# run all linters
[parallel]
lint: js_lint py_lint db_lint

# nicely clean all build artifacts and caches
clean: js_clean py_clean build_clean

# aggressively destroy everything and rebuild it
nuke: js_nuke py_nuke db_nuke
		rm -rf $TMP_DIRECTORY/* || true
		mkdir -p $TMP_DIRECTORY

		rm -rf .git/hooks/* || true


TEMPLATE_UPDATE_NOTICE := """
This project is being updated using the python copier tool with the upstream template.

However, there are some changes which are not automatically applied:

- Update skips all javascript updates. View significant changes:
	 git log -- web/ \":(exclude)web/package.json\" \":(exclude)web/pnpm*\" \":(exclude)web/mise.toml\"
- Update skips .tool-versions updates
- You'll need to manually review conflicts of which there will be many
	- 'incoming' change in a diff is the template changes.
"""

# syncs the project with the upstream python-starter-template repo.
update_from_upstream_template:
		@just _banner_echo "Running Upgrade From Template"

		@echo "{{ TEMPLATE_UPDATE_NOTICE }}"

		uv tool run --with jinja2_shell_extension \
			copier update@latest update \
			--trust --skip-tasks --skip-answered --vcs-ref=HEAD \
			--exclude web \
			--exclude migrations/versions/ \
			--exclude app/generated/ \
			--exclude pyproject.toml \
			--exclude uv.lock \
			--exclude tests/integration/__snapshots__ \
			--exclude .service-versions \
			--exclude .tool-versions \
			--exclude .github/instructions \
			--exclude .github/copilot-instructions.md \
			--exclude .cursor \
			--exclude .gemini \
			--exclude .claude \
			--exclude .opencode

		# TODO maybe rerun autogen?

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
import 'just/setup.just'
