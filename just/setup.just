#######################
# Local Developer Setup
#######################

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

	mise install

	# bonus packages for a fancy devprod experience
	@if [[ "{{flags}}" =~ "--extras" ]]; then \
		echo "Removing sample git hooks..."; \
		rm .git/hooks/*.sample || true; \
		\
		echo "Installing git hooks..."; \
		lefthook install; \
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

	@if [ ! -f .config/mise.local.toml ]; then \
		cp .config/mise.local.toml-template .config/mise.local.toml; \
		echo "Edit '{{CYAN}}.config/mise.local.toml{{NORMAL}}' to your liking."; \
	fi

	@echo 'If you are using localias, run `{{CYAN}}just localias{{NORMAL}}` to start the daemon'

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
