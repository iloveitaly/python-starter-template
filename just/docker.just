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

	docker run --rm \
		-v /etc/hosts:/etc/hosts \
		-v /var/run/docker.sock:/var/run/docker.sock \
		--cap-add NET_ADMIN \
		-e ETCHOSTS_ALL=1 \
		costela/docker-etchosts -once

	cat /etc/hosts

# stop all containers and remove the images
down: db_down
	docker compose down

# open redis database in the default macos GUI
redis_open: _dev_only
	open "$REDIS_URL" -a TablePlus
