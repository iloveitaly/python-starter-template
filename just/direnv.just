#######################
# Direnv Extensions
#
# Primarily to workout direnv limitations:
# - DIRENV_* vars are always included in the export
# - layout related vars are included as well
# - Path modifications are included
# - There is not an intuitive way to export a specific env file as json
#
# The logic here requires RENDER_DIRENV logic in the top-level .envrc
#
#######################

jq_script := """
with_entries(
	select((
		(.key | startswith("DIRENV_") | not)
		and (.key | IN("VIRTUAL_ENV", "VENV_ACTIVE", "UV_ACTIVE", "PATH", "OP_SERVICE_ACCOUNT_TOKEN") | not)
	))
)
"""

# TODO report this upstream to direnv, this is an insane workaround :/
# target a specific .env file (supports direnv features!) for export as a JSON blob
@direnv_export target="":
	([ ! -n "{{target}}" ] || [ -f "{{target}}" ]) || (echo "{{target}} does not exist"; exit 1)
	[ "{{target}}" != ".envrc" ] || (echo "You cannot use .envrc as a target"; exit 1)

	# without a clear env (env -i), any variables set in your shell (via ~/.exports or similar) will *not* be included
	# in `direnv export`. I originally discovered this because PYTHON* vars were not being exported because they were set
	# globally. To work around this we clear the environment, outside of the PATH + HOME required for direnv configuration.
	# OP_SERVICE_ACCOUNT_TOKEN is also included since on CI this is effectively global state that enables 1p access.
	# When run on your local machine, 1p global state may be persisted elsewhere, so this would be a noop.
	env -i HOME="$HOME" PATH="$PATH" OP_SERVICE_ACCOUNT_TOKEN="${OP_SERVICE_ACCOUNT_TOKEN:-}" op daemon -d
	# OP_* variables are passed through to avoid having to hardcode the account token or vault uid
	# depending on your secret setup, you may want to use a different approach
	env -i HOME="$HOME" PATH="$PATH" \
		OP_SERVICE_ACCOUNT_TOKEN="${OP_SERVICE_ACCOUNT_TOKEN:-}" OP_VAULT_UID="${OP_VAULT_UID:-}" \
		RENDER_DIRENV="{{target}}" \
		direnv export json | jq -r '{{jq_script}}'

	# TODO the `op daemon -d` hack above is to workaround a op bug:
	# https://1password-devs.slack.com/archives/C03NJV34SSC/p1733771530356779
	# https://github.com/direnv/direnv/issues/662

# JSON dump of the test environment secrets, used for local pytest runs (direnv.py for more details)
@direnv_export_ci:
	env -i HOME="$HOME" PATH="$PATH" \
		OP_SERVICE_ACCOUNT_TOKEN="${OP_SERVICE_ACCOUNT_TOKEN:-}" \
		CI=true direnv export json | jq -r '{{jq_script}}'

# export env variables for a particular file in a format docker can consume
[doc("Export as docker '-e' params: --params\nExport as shell: --shell\nExport as dokku: --dokku")]
@direnv_export_docker target *flag:
	# NOTE @sh below does NOT handle newlines, tabs, etc in ANSI-C format like direnv does
	#      https://github.com/iloveitaly/direnv/blob/1a39d968c165fddff3b9a4c5538025d71f73ee43/internal/cmd/shell_bash.go#L97
	#      this could cause issues for us, although it seems as though @sh just includes the literal newline or tab char
	# 		 instead of the escaped version, which is most likely fine.
	# dokku wants all environment variables on a single line, which is why we join them with a space

	if {{ if flag == "--params" { "true" } else { "false" } }}; then; \
		just direnv_export "{{target}}" | jq -r 'to_entries | map("--env \(.key)=\(.value)") | join(" ")'; \
	elif {{ if flag == "--shell" { "true" } else { "false" } }}; then; \
		just direnv_export "{{target}}" | jq -r 'to_entries[] | "export \(.key)=\(.value | @sh)"'; \
	elif {{ if flag == "--dokku" { "true" } else { "false" } }}; then; \
		just direnv_export "{{target}}" | jq -r '[to_entries[] | "\(.key)=\(.value | @base64)"] | join(" ")'; \
	else; \
		just direnv_export "{{target}}" | jq -r 'to_entries[] | "\(.key)=\(.value)"'; \
	fi

	# last case is exporting as a docker file (i.e. no export)
	# TODO note this is not currently in use, so we'll probably have to tweak it in the future

BASH_EXPORT_PREAMBLE := """
# Description: easy source-able bash script in case a user doesn't want to bother with direnv and friends
# More info: https://github.com/iloveitaly/python-starter-template#simple-mode

# we assume a venv is already setup using `just setup`
source .venv/bin/activate

# `mise` is installed in ~/.local/bin by default, we assume the user is not using mise across their installation
# so we force the path to be added.
export PATH="$HOME/.local/bin:$PATH"

if command -v mise >/dev/null 2>&1; then
	eval "$(mise activate)"
else
	echo "[direnv_bash_export] mise not found, skipping activation" >&2
fi

# just runner completions make life a *lot* better
if command -v just >/dev/null 2>&1; then
	eval "$(just --completions $(basename "$SHELL"))"
else
	echo "[direnv_bash_export] just not found, skipping completions." >&2
fi

## BEGIN DIRENV EXPORT
"""

# export direnv variables as a bash script to avoid using direnv and mutating your environment configuration
[script]
direnv_bash_export: _dev_only
	# TODO required direnv allow otherwise it won't work
	target_file="env/$(whoami).local.sh"

	cat << 'EOF' > "$target_file"
	{{BASH_EXPORT_PREAMBLE}}
	EOF

	just direnv_export_docker "" --shell >> "$target_file"
	echo $'\n\n## END DIRENV EXPORT' >> "$target_file"

	echo $'\n'
	echo "File generated: $target_file"
	echo "Source using 'source $target_file'"
