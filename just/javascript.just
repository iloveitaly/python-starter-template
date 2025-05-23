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

# run all javascript linters, optionally include a list of files to check
js_lint +FILES=".":
	# TODO support GITHUB_ACTIONS/CI formatting
	{{_pnpm}} prettier --check {{FILES}}

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
	# you may want to customize the application target, depending on you are structuring your frontend code
	# jq is here to pretty print the output
	LOG_LEVEL=error uv run python -m app.cli dump-openapi \
		--app-target internal_api_app \
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
[script]
_js_sync-engine-versions: _dev_only
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
