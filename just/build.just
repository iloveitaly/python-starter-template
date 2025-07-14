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
# We need to escape double quotes in commit messages.
GIT_DESCRIPTION := `git log -1 --format=%s | sed 's/"/\\"/g'`
BUILD_CREATED_AT := `date -u +%FT%TZ`
RAILPACK_BUILD_METADATA := (
	'--env BUILD_COMMIT="' + GIT_SHA + '" ' +
	'--env BUILD_DESCRIPTION="' + GIT_DESCRIPTION + '" ' +
	'--env BUILD_CREATED_AT="' + BUILD_CREATED_AT + '" '
)

FRONTEND_IMAGE := "ghcr.io/railwayapp/railpack-frontend:latest"

# architecture images will be running on
BUILD_PLATFORM := "linux/arm64/v8"

# NOTE production secrets are *not* included in the image, they are set on deploy
PYTHON_RAILPACK_PREPARE_CMD := "railpack prepare ." + \
	" --plan-out railpack.json" + \
	" --info-out railpack-info.json" + \
	" --env PYTHON_ENV=production" + \
	" $(just direnv_export_docker '" + SHARED_ENV_FILE +"' --params)"

PYTHON_RAILPACK_BUILD_CMD := "docker buildx build ." + \
	" --build-arg BUILDKIT_SYNTAX=" + FRONTEND_IMAGE + \
	" " + RAILPACK_BUILD_METADATA + \
	" -f railpack.json" + \
	" -t " + PYTHON_IMAGE_TAG + \
	" --platform linux/amd64" + \
	" --cache-to type=inline" + \
	" --cache-from " + PYTHON_PRODUCTION_IMAGE_NAME + ":latest" + \
	" --label org.opencontainers.image.revision='" + GIT_SHA + "'" + \
	" --label org.opencontainers.image.created='" + BUILD_CREATED_AT + "'" + \
	' --label org.opencontainers.image.source="$(just _repo_url)"' + \
	' --label org.opencontainers.image.description="Primary application deployment image"' + \
	' --label build.run_id="$(just _build_id)"'

# Production assets bundle public "secrets" (safe to expose publicly) which are extracted from the environment
# for this reason, we need to emulate the production environment, then build the assets statically.
# Also, we can't just mount /app/build/server with -v since the build process removes the entire /app/build directory.
# Some ENV var are set for us, like NODE_ENV: https://railpack.com/docs/providers/node#environment-variables
JAVASCRIPT_RAILPACK_PREPARE_CMD := "railpack prepare " + WEB_DIR + \
	" --plan-out " + WEB_DIR + "/railpack.json" + \
	" --info-out " + WEB_DIR + "/railpack-info.json" + \
	" --env VITE_BUILD_COMMIT=" + GIT_SHA + \
	" $(just direnv_export_docker '" + JAVASCRIPT_SECRETS_FILE + "' --params) " + \
	" $(just direnv_export_docker '" + SHARED_ENV_FILE + "' --params)"

JAVASCRIPT_RAILPACK_BUILD_CMD := "docker buildx build " + WEB_DIR + \
	" --build-arg BUILDKIT_SYNTAX=" + FRONTEND_IMAGE + \
	" " + RAILPACK_BUILD_METADATA + \
	" -f " + WEB_DIR + "/railpack.json" + \
	" -t " + JAVASCRIPT_IMAGE_TAG + \
	" --platform linux/amd64" + \
	" --cache-to type=inline" + \
	" --cache-from " + JAVASCRIPT_PRODUCTION_IMAGE_NAME + ":latest" + \
	" --label org.opencontainers.image.description=\"Used for building javascript assets, not for deployment\""

# .env file without any secrets that should exist on all environments
SHARED_ENV_FILE := "env/all.sh"

# .env file with production secrets for python
PYTHON_PRODUCTION_ENV_FILE := "env/production.backend.sh"

# .env file with production variables that are safe to share publicly (frontend)
JAVASCRIPT_SECRETS_FILE := "env/production.frontend.sh"

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

# within railpack, this is where the SPA client assets are built
JAVASCRIPT_CONTAINER_BUILD_DIR := "/app/build/client"
# outside of railpack, within the python application folder, this is where the SPA assets are stored
JAVASCRIPT_PRODUCTION_BUILD_DIR := "public"

# build the javascript assets by creating an image, building assets inside the container, and then copying them to the host
build_javascript: _production_build_assertions
	@just _banner_echo "Building JavaScript Assets in Container..."
	rm -rf "{{JAVASCRIPT_PRODUCTION_BUILD_DIR}}" || true

	{{JAVASCRIPT_RAILPACK_PREPARE_CMD}}
	{{JAVASCRIPT_RAILPACK_BUILD_CMD}}

	@just _banner_echo "Extracting JavaScript Assets from Container..."

	# Cannot extract files out of a image, only a container. We create a tmp container to extract assets.
	docker rm tmp-js-container || true
	docker create --name tmp-js-container {{JAVASCRIPT_IMAGE_TAG}}
	docker cp tmp-js-container:{{JAVASCRIPT_CONTAINER_BUILD_DIR}} "{{JAVASCRIPT_PRODUCTION_BUILD_DIR}}"

# dump railpack-generated plan for manual build and production debugging
build_javascript_dump:
	{{JAVASCRIPT_RAILPACK_PREPARE_CMD}}

# inject a shell where the javascript build fails, helpful for debugging railpack build failures
build_javascript_debug: build_javascript_dump
	# note that you *may* run into trouble using the interactive injected shell if you are using an old builder version
	# Force the latest builder: `docker buildx use orbstack`

	BUILDX_EXPERIMENTAL=1 docker buildx debug --invoke /bin/sh build -f {{WEB_DIR}}/railpack.json {{WEB_DIR}}

# support non-macos installations for github actions
_build_requirements:
	@if ! which railpack > /dev/null; then \
		echo "railpack is not installed. Installing...."; \
		{{ if os() == "macos" { "curl -sSL https://railpack.com/install.sh | sh -s -- --bin-dir ~/.local/bin" } else { "curl -sSL https://railpack.com/install.sh | sh" } }}; \
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

# build the docker container using railpack
build: _build_requirements _production_build_assertions build_javascript
	@just _banner_echo "Building Python Image..."
	{{PYTHON_RAILPACK_PREPARE_CMD}}
	{{PYTHON_RAILPACK_BUILD_CMD}}

build_push: _production_build_assertions
	# JS image is not used in prod, but is used for railpack caching, so we push to the registry
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
build_dive: _dev_only (_brew_check_and_install "dive")
	dive "{{PYTHON_IMAGE_TAG}}"

# dump railpack-generated plan for manual build and production debugging
build_dump:
	{{PYTHON_RAILPACK_PREPARE_CMD}}

# clear out railpack and other artifacts specific to production containers
build_clean:
	rm -rf railpack.json railpack-info.json {{WEB_DIR}}/railpack.json {{WEB_DIR}}/railpack-info.json || true

# inject a shell where the build fails, helpful for debugging railpack build failures
build_debug: build_dump
	# note that you *may* run into trouble using the interactive injected shell if you are using an old builder version
	# Force the latest builder: `docker buildx use orbstack`

	BUILDX_EXPERIMENTAL=1 docker buildx debug --invoke /bin/sh build -f railpack.json .

# instead of using autogenerated Dockerfile, build from the dumped Dockerfile which can be manually modified for development
build_from-dump:
	{{PYTHON_RAILPACK_BUILD_CMD}}

# open up a bash shell in the last built container, helpful for debugging production builds
build_shell: build
	docker run -it {{PYTHON_IMAGE_TAG}} bash -l

# open up a *second* shell in the *same* container that's already running
build_shell-exec:
	docker exec -it $(docker ps -q --filter "ancestor={{PYTHON_IMAGE_TAG}}") bash -l

# TODO https://discord.com/channels/1106380155536035840/1318603119990538340/1318603119990538340
# run the container locally, as if it were in production (against production DB, resources, etc)
build_run-as-production procname="api" image_name=PYTHON_IMAGE_TAG:
	# NOTE that resources are limited to a production-like environment, change if your production requirements are different
	docker run -p ${JAVASCRIPT_SERVER_PORT}:80 \
		--memory=1g --cpus=2 \
		$(just direnv_export_docker "env/production.backend.sh" --params) \
		--platform {{BUILD_PLATFORM}} \
		"{{image_name}}" \
		"$(just _extract_proc "{{procname}}")"

# extract worker start command from Procfile, useful for defining entrypoints in docker containers
[script]
_extract_proc procname:
	[ -n "{{procname}}" ] || exit 0
	yq -r '.{{procname}}' Procfile
