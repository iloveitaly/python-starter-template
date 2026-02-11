##########################
# Dev Container Management
##########################

# Use --fast to avoid waiting until the containers are healthy, useful for CI runs
[script]
[arg("fast", long, help="skip waiting for healthy containers", value="false")]
[arg("latest", long, help="pull latest images and recreate services", value="false")]
up fast="false" latest="false": _dev_only
	# if images have already been pulled, this ensures the latest versions are pulled so they match with
	# CI or other environments that are pulling fresh versions of the images
	if [[ "{{latest}}" == "true" ]]; then
		docker compose pull
	fi

	# force a restart to pick up the latest pulled images
	if [[ "{{latest}}" == "true" ]]; then
		docker compose up -d --force-recreate {{ if fast == "true" { "" } else { "--wait" } }}
		just py_cli write-versions
	else
		docker compose up -d {{ if fast == "true" { "" } else { "--wait" } }}
	fi

	# enables us to (a) avoid exposing ports to the host machine and (b) have dns names for each service in CI
	# this is done for us on macOS via OrbStack. Without this, the `DOCKER_POSTGRES` binary approach would not work.
	# this approach works well on Linux, but not on WSL. Default WSL configuration does not assign each container a unique
	# address.
	[[ -n "${CI:-}" ]] && sudo $(which uvx) docker-hosts@latest || true

# stop all containers and remove the images
down: db_down
	docker compose down

# open redis database in the default macos GUI
redis_open: _dev_only
	open "$REDIS_URL" -a TablePlus
