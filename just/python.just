#######################
# Python
#######################

# this is used for jinja + HTML linting, if you put templates elsewhere, you'll need to update this
JINJA_TEMPLATE_DIR := "app/templates"

# create venv and install packages
py_setup:
	# `mise env`` will generate a venv if it DNE
	# TODO feels like there should be a cleaner way to get mise to regenerate the venv...
	[ -d ".venv" ] || mise env

	# don't include debugging-extras on CI
  # note that the packages used on CI are different than production, which introduces some risk
  # `--no-sources` would prevent local dev packages from being used, if you want to mirror prod in CI more closely
  #   https://github.com/astral-sh/uv/issues/9258#issuecomment-2499541207
	if [ -z "${CI:-}" ]; then \
		uv sync --all-groups; \
	else \
		uv sync --no-editable; \
	fi

	# important for CI to install browsers for playwright
	# the installation process is fast enough (<10s) to eliminate the need for attempting to cache via GHA
	# if this turns out not to be true, we should implement: https://github.com/hirasso/thumbhash-custom-element/blob/main/.github/workflows/tests.yml

	# TODO why should we use --only-shell here? can we extract this out and run it after we update the packages as well?

	if [ -z "${CI:-}" ]; then \
		uv run playwright install chromium; \
	else \
		uv run playwright install chromium --only-shell; \
	fi

# clean entire py project without rebuilding
py_clean:
	# pycache should never appear because of PYTHON* vars

	rm -rf .pytest_cache .ruff_cache .venv || true
	rm -rf tests/**/snapshot_tests_failures || true
	rm -rf $PLAYWRIGHT_BROWSERS_PATH || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete || true

	# TODO should remove pnpm global cache:   pnpm store path
	# rm -rf $(pnpm store path)


# rebuild the venv from scratch
py_nuke: py_clean py_setup

py_upgrade:
	# https://github.com/astral-sh/uv/issues/6794
	uv sync -U --group=debugging-extras
	uv tool upgrade --all
	git add pyproject.toml uv.lock

# open up a python development server
py_dev:
	# if the server doesn't quit perfectly, it can still consume the port, let's avoid having to think about that
	kill -9 $(lsof -t -i :${PYTHON_SERVER_PORT}) 2>/dev/null || true
	PORT=$PYTHON_SERVER_PORT uv run python main.py

py_play:
	./playground.py

# TODO should have additional tool for workers and all server processes

# run all linting operations and fail if any fail
[script]
py_lint +FILES=".":
	# + indicates one more arguments being required in Justfile syntax

	# NOTE this is important: we want all operations to run instead of fail fast
	set +e

	# TODO we should either abstract this out or remove it...
	# Define a more detailed colored PS4 without current directory so -x output is easier to read
	setopt prompt_subst
	export PS4='%F{green}+%f '
	set -x

	if [ -n "${CI:-}" ]; then
		# TODO I'm surprised that ruff doesn't auto detect github... need to double check on this
		uv tool run ruff check --output-format=github {{FILES}} || exit_code=$?
		uv tool run ruff format --check {{FILES}} || exit_code=$?
		uvx detect-shadowed-modules@latest || exit_code=$?

		uv run pyright {{FILES}} --outputjson > pyright_report.json || exit_code=$?
		# TODO this is a neat trick, we should use it in other places too + document
		# https://docs.github.com/en/actions/writing-workflows/choosing-what-your-workflow-does/workflow-commands-for-github-actions#setting-a-warning-message
		# https://github.com/jakebailey/pyright-action/blob/b7d7f8e5e5f195796c6f3f0b471a761a115d3b2c/src/main.ts#L62
		jq -r \
		--arg root "$GITHUB_WORKSPACE/" \
		'
			.generalDiagnostics[] |
			.file as $file |
			($file | sub("^\\Q\($root)\\E"; "")) as $rel_file |
			"::\(.severity) file=\($rel_file),line=\(.range.start.line),endLine=\(.range.end.line),col=\(.range.start.character),endColumn=\(.range.end.character)::\($rel_file):\(.range.start.line): \(.message)"
		' < pyright_report.json
		rm pyright_report.json

		# check jinja2 template language
		uv run j2lint --extension j2,html {{JINJA_TEMPLATE_DIR}} --json > j2link_report.json || exit_code=$?
		jq -r '(.ERRORS[] | "::\(if .severity == "HIGH" then "error" else "warning" end) file=\(.filename),line=\(.line_number),title=\(.id)::\(.message)"), (.WARNINGS[] | "::warning file=\(.filename),line=\(.line_number),title=\(.id)::\(.message)")' < j2link_report.json
		rm j2link_report.json
	else
		uv tool run ruff check {{FILES}} || exit_code=$?
		uv run pyright {{FILES}} || exit_code=$?
		uvx detect-shadowed-modules@latest || exit_code=$?
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
	uv tool run ruff format

	uv run djlint --profile=jinja --reformat {{JINJA_TEMPLATE_DIR}}

	# NOTE pyright and other linters do not have an automatic fix flow

# build js for py e2e tests
py_js-build:
	# integration tests should mimic production as closely as possible
	# to do this, we build the app and serve it like it will be served in production
	export PNPM_GLOBAL_FLAGS="--silent" && {{EXECUTE_IN_TEST}} just js_build

PYTEST_COV_PARAMS := "--cov --cov-report=html:${TEST_RESULTS_DIRECTORY}/htmlcov"

# run tests with the exact same environment that will be used on CI
[script]
py_test:
	# Define a more detailed colored PS4 without current directory so -x output is easier to read
	setopt prompt_subst
	export PS4='%F{green}+%f '
	set -x

	# TODO we don't need to see all of the details for this part of the build, since we are primarily testing javascript

	# TODO I wonder if I could make EXECUTE_IN_TEST blank if in the test environment...
	# NOTE unfortunately, because of the asyncio loop + playwright, we need to run the playwright integration tests separately
	if [[ -n "${CI:-}" ]]; then
		just _banner_echo "Building Javascript for Integration Tests"
		just py_js-build
		just _banner_echo "Running Non-Integration Tests"
		uv run pytest . --verbosity=2 --ignore tests/integration {{PYTEST_COV_PARAMS}}
		just _banner_echo "Running Integration"
		uv run pytest tests/integration --verbosity=2 --cov-append {{PYTEST_COV_PARAMS}}
	else
		# when not running in CI, JS is built automatically
		{{EXECUTE_IN_TEST}} uv run pytest . --verbosity=2 --ignore tests/integration {{PYTEST_COV_PARAMS}}
		{{EXECUTE_IN_TEST}} uv run pytest tests/integration --verbosity=2 --cov-append {{PYTEST_COV_PARAMS}}
	fi

# regenerate all python generated files
[doc("Optional flag: --watch")]
py_generate *flag:
	if {{ if flag == "--watch" { "true" } else { "false" } }}; then; \
		watchexec -e py --ignore 'tests/' --ignore 'migrations/' --ignore 'playground/' -- just _py_generate; \
	else; \
		just _py_generate; \
	fi

# regenerate all files, written as a helper so the file watcher can easily rerun
_py_generate:
	mkdir -p app/generated

	# TODO may be able to use uvx in the future, but uv run for now has eliminated

	# generate typed python routes from react-router routes
	# `mise exec` is required for the pnpm execution
	mise exec -- uv run react-router-routes \
		app/generated/react_router_routes.py \
		--directory {{WEB_DIR}}

	# generate typed fastapi routes, for python, from the fastapi app
	LOG_LEVEL=ERROR uv run generate-fastapi-typed-routes \
		--app-module app.server:api_app \
		--output app/generated/fastapi_typed_routes.py

# open playwright trace viewer on last trace zip. --remote to download last failed remote trace
py_playwright_view_trace remote="": _dev_only
		mkdir -p ${PLAYWRIGHT_RESULT_DIRECTORY}

		# helpful to download to unique folder for two reasons: (a) easier to match up to web GHA view and (b) eliminates risk of gh-cli erroring out bc the directory already exists
		if [ "{{remote}}" = "--remote" ]; then \
				failed_run_id=$(just _gha_last_failed_run_id) && \
				mkdir -p ${PLAYWRIGHT_RESULT_DIRECTORY}/${failed_run_id} && \
				gh run --dir ${PLAYWRIGHT_RESULT_DIRECTORY}/${failed_run_id} download $failed_run_id; \
				echo "{{BLUE}}Downloaded remote GHA run to ${PLAYWRIGHT_RESULT_DIRECTORY}/${failed_run_id}{{NORMAL}}"; \
		fi

		# NOTE it's insane, but fd does not have a "find last modified file"
		# https://github.com/sharkdp/fd/issues/196
		uv run playwright show-trace $(fd --no-ignore-vcs . ${PLAYWRIGHT_RESULT_DIRECTORY} -e zip -t f --exec-batch stat -f '%m %N' | sort -n | tail -1 | cut -f2- -d" ")

# download the visual snapshots from the last failed playwright run, useful for updating non-macos screenshot versions
py_playwright_visual-download: _dev_only
	failed_run_id=$(just _gha_last_failed_run_id) && \
		rm -rf ${PLAYWRIGHT_RESULT_DIRECTORY}/${failed_run_id} && \
		mkdir -p ${PLAYWRIGHT_RESULT_DIRECTORY}/${failed_run_id} && \
		gh run --dir ${PLAYWRIGHT_RESULT_DIRECTORY}/${failed_run_id} download $failed_run_id && \
		cp -R ${PLAYWRIGHT_RESULT_DIRECTORY}/${failed_run_id}/test-results/${PLAYWRIGHT_VISUAL_SNAPSHOT_DIRECTORY}/ ${PLAYWRIGHT_VISUAL_SNAPSHOT_DIRECTORY}/

# open chromium to record playwright interactions for integration tests and dump them to a file
[script]
py_playwright-record: _dev_only
	mkdir -p tmp/playwright
	recorded_interaction=tmp/playwright/$(date +%m-%d-%s).py

	uv run playwright codegen \
		--target python-pytest \
		--output $recorded_interaction \
		https://${JAVASCRIPT_SERVER_HOST}

	echo $recorded_interaction
	pbcopy < $recorded_interaction

# TODO why in the python module?
# open mailpit web ui, helpful for inspecting emails
py_mailpit_open:
	open "https://$(echo $SMTP_URL | cut -d'/' -f3 | cut -d':' -f1)"

# run py-spy on all python processes with a cwd matching the current project
py_spy:
	ps -eo pid,command | \
		awk -v dir="$(pwd)" '$2 ~ /python/ && system("lsof -p " $1 " 2>/dev/null | grep -q " dir) == 0 {print $1}' | \
		xargs -I{} sudo py-spy dump --pid {}

# avoid using the app entrypoint shortcut to avoid having to modify the name across different projects
# consistent CLI entrypoint for the python app CLI
py_cli *args:
	uv run python -m app.cli {{args}}
