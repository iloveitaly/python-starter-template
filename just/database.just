##############################################
# Database Migrations
#
# Goal is to have similar semantics to rails.
##############################################

# Helper to run a command in both dev and test environments, with a label for the banner
# It does require you to pass the command as a string, which is a bit of a pain.
# It does NOT change the DATABASE_URL, if you need to pass the TEST_DATABASE_URL you must do that
# manually and cannot use this helper.
_run_in_dev_and_test label *command: _dev_only
	@just _banner_echo "Running in dev environment: {{label}}"
	{{command}}

	@just _banner_echo "Running in test environment: {{label}}"
	{{EXECUTE_IN_TEST}} {{command}}

# separate task for the db to support db_reset
db_up: _dev_only
	docker compose up -d --wait postgres

# TODO may need to run `docker rm $(docker ps -aq)` as well
# TODO docker down does not exit 1 if it partially failed
# turn off the database *and* completely remove the data
db_down: _dev_only
	docker compose down --volumes postgres

# completely destroy the dev and test databases, destroying the containers and rebuilding them
db_reset_hard: _dev_only db_down db_up db_migrate db_seed

# this is a very aggressive termination SQL which terminates all DB connections and immediately drops schema
DB_TERMINATE_AND_RESET_SCHEMA := "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = current_database() AND pid <> pg_backend_pid(); DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

# When running postgres CLI binaries, we do so inside the container. Here's why:
#
# - Not all devs have psql* installed, and brew does not install binary aliases by default
# - Using the image versions ensures the exact same version of the binaries are used everywhere
#
# However, this does complicate interactions:
#
# * Locally, I'm using OrbStack which has nice friendly domain references that work anywhere. No problems there.
# * In other environments (CI/Linux/WSL), this is not the case. Since we are using `run` the pg binaries are running
#   in a new container so `localhost` references won't work.
#
# In order to fix this we must replicate the *.orb domains on CI by updating the /etc/hosts file.
#
# -T flag: Disables pseudo-TTY allocation
#   * Interactive commands (psql) need TTY (-t)
#   * Non-interactive commands (pg_dump) don't need TTY and can fail with TTY (-T)
#   * pg_dump with output redirection (> file) works best without TTY
DOCKER_POSTGRES := "docker compose run --rm -T postgres"

# drop all DB connections and then drop all tables and completely reset the schema
db_reset_schema: _dev_only
	{{DOCKER_POSTGRES}} psql $DATABASE_URL -c "{{DB_TERMINATE_AND_RESET_SCHEMA}}"
	{{DOCKER_POSTGRES}} psql $TEST_DATABASE_URL -c "{{DB_TERMINATE_AND_RESET_SCHEMA}}"

# destroys all data in the dev and test databases, leaves the containers running
db_reset: _dev_only db_reset_schema db_migrate db_seed

# TODO can we do something in SQLModel to sync new columns to the DB as well
# wipe, migrate, and set database state to the latest (head) model configuration. Do not use in production, always use migrations
db_reset_head: _dev_only db_reset_schema db_migrate db_migrate_head db_seed

# destroy and rebuild the database from the ground up, without mutating migrations or recreating database containers (unlike nuke)
db_destroy: _dev_only db_reset db_migrate db_seed

db_lint:
	uv run alembic check

	# TODO there's also a more advanced github integration, but seems a bit cleaner:
	# https://squawkhq.com/docs/github_app

	# TODO don't fail on warnings https://github.com/sbdchd/squawk/issues/348
	# TODO remove rule exclusion when https://github.com/sbdchd/squawk/issues/392 is fixed
	LOG_LEVEL=error uv run alembic upgrade head --sql | \
		squawk --reporter=json \
			--exclude=prefer-text-field --pg-version=$(jq -r '.postgres' .service-versions); \

# open the database in the default macos GUI
db_open: _dev_only
	# TablePlus via Setapp is a great option here
	open $DATABASE_URL

# tui to interact with the database
db_play: _dev_only
	uvx pgcli@latest $DATABASE_URL

# run migrations on dev and test
db_migrate: _not_production
	# if this folder is wiped, you'll get a strange error from alembic
	mkdir -p migrations/versions

	# dev database is created automatically, but test database is not. We want to fail loudly when creation of the test DB fails.
	# PostgreSQL does not support IF NOT EXISTS on CREATE DATABASE which is why we run the WHERE NOT EXISTS query first.
	echo "SELECT 'CREATE DATABASE ${TEST_DATABASE_NAME}' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '${TEST_DATABASE_NAME}')\gexec" | \
		{{DOCKER_POSTGRES}} psql "$DATABASE_URL"

	@just _banner_echo "Migrating Database"

	uv run alembic upgrade head

	[ -n "${CI:-}" ] || (just _banner_echo "Migrating Test Database" && {{EXECUTE_IN_TEST}} uv run alembic upgrade head)

# quickly reset the entire database, migrate, seed, *and* sync database state to what the latest model configuration is
db_migrate_head: _dev_only
	just _run_in_dev_and_test "db_migrate_head" 'uv run python -c "import app.models; from app.configuration.database import create_db_and_tables; create_db_and_tables()"'

# pick a migration to downgrade to
db_downgrade: _dev_only
	alembic_target_id=$(LOG_LEVEL=ERROR uv run alembic history | fzf --delimiter '[->\s,]+' --bind 'enter:become(echo {2})') && \
		just _banner_echo "Downgrading Dev Database..." && \
		uv run alembic downgrade $alembic_target_id && \
		just _banner_echo "Downgrading Test Database..." && \
		{{EXECUTE_IN_TEST}} uv run alembic downgrade $alembic_target_id

# a common workflow is: add more columns, add migration, run migration; revise, downgrade migration, regenerate migration, rerun migrations
db_downgrade_last:
	uv run alembic downgrade -1
	{{EXECUTE_IN_TEST}} uv run alembic downgrade -1

# TODO I don't think we really want to migrate the database automatically. Instead, want this to be an independent command that we can call inside the reset and other operations.
# add seed data to dev and test
db_seed: _not_production db_migrate
	@just _banner_echo "Seeding Database"

	# you WILL get errors at this stage if you have SQLModel mutations that do not have an associated migration
	# and if you rely on them within your seeding process
	uv run python migrations/seed.py

	[ -n "${CI:-}" ] || (just _banner_echo "Seeding Test Database" && {{EXECUTE_IN_TEST}} uv run python migrations/seed.py)

# TODO you can't preview what the migration will look like before naming it?
# generate migration based on the current state of the database
[script]
db_generate_migration migration_name="": _dev_only
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

# rm migrations and regenerate: only for use in early development
db_nuke: _dev_only
	# I personally hate having a nearly-greenfield project with a bunch of migrations from DB schema iteration
	# this should only be used *before* you've launched and prod and don't need properly migration support

	# first, wipe all of the existing migrations
	rm -rf migrations/versions/* || true

	just db_reset_schema
	just db_generate_migration "initial_commit"

# enable SQL debugging on the postgres database
db_debug: _dev_only
	{{DOCKER_POSTGRES}} psql -U $POSTGRES_USER -d $POSTGRES_DB -c "ALTER SYSTEM SET log_statement = 'all'" -c "SELECT pg_reload_conf();"

# disable SQL debugging on the postgres database
db_debug_off: _dev_only
	{{DOCKER_POSTGRES}} psql -U $POSTGRES_USER -d $POSTGRES_DB -c "ALTER SYSTEM SET log_statement = 'none'" -c "SELECT pg_reload_conf();"

# generate an AI prompt to help with writing SQL from the local development database (better when it's filled with real data)
db_prompt: _dev_only
	uvx llm-sql-prompt@latest $DATABASE_URL --all

# dump the production database locally, obviously this is dangerous
[script]
db_dump_production: _dev_only
	echo "{{ BLUE }}Enter the op:// reference or postgres:// URL for the production DB:{{ NORMAL }}"
	echo "{{ BLUE }}e.g., op://Dev/prod DB/db-connection-string or postgres://user:pass@host:5432/dbname{{ NORMAL }}"
	read db_ref

	if [[ "$db_ref" == postgres://* ]]; then
		DB_URL="$db_ref"
	else
		DB_URL=$(op read "$db_ref")
	fi

	mkdir -p $TMP_DIRECTORY/database-backups
	dump_file="$TMP_DIRECTORY/database-backups/$(date '+%Y-%m-%d_%s')_production.dump"
	echo "Dumping production database..."

	# custom format: compressed, supports selective restore with pg_restore
	pg_dump "$DB_URL" --format c > "$dump_file"

	echo "Created file: $dump_file"
	echo "Example restore: \n{{ BLUE }}pg_restore --no-owner --no-privileges --if-exists --clean -d \$DATABASE_URL $dump_file{{ NORMAL }}"

# create a backup file of the local dev database
db_dump_dev: _dev_only
	mkdir -p $TMP_DIRECTORY/database-backups
	@echo "{{GREEN}}Dumping dev database...{{NORMAL}}"

	{{DOCKER_POSTGRES}} pg_dump "$DATABASE_URL" --format c > "$TMP_DIRECTORY/database-backups/$(date '+%Y-%m-%d_%s')_dev.dump"

	@echo "Created file: {{BLUE}}$TMP_DIRECTORY/database-backups/$(date '+%Y-%m-%d_%s')_dev.dump{{NORMAL}}"
	@echo "{{GREEN}}Example pg_restore command:{{NORMAL}}\n{{ BLUE }}pg_restore --no-owner --no-privileges --if-exists --clean -d \$DATABASE_URL \$TMP_DIRECTORY/database-backups/$(date '+%Y-%m-%d_%s')_dev.dump{{ NORMAL }}"
