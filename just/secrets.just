#######################
# Secrets (via 1Password)
#######################

_secrets_service-token CONTEXT WRITE_PERMISSION="false":
	# this can occur if .envrc fails because of an expired service token, it's also hard to notice and understand exactly
	# what to do here, so let's make it clear to the user what they need to do to fix it.
	@[[ -n "${OP_VAULT_UID:-}" ]] || { \
		echo "{{RED}}error: OP_VAULT_UID must be set in order to generate a service account token{{NORMAL}}" >&2; \
		echo "{{BLUE}}Set it with: export OP_VAULT_UID=5pxsyszwmfyzhzsz5ncglvo3ku{{NORMAL}}" >&2; \
		exit 1; \
	}

	# if OP_SERVICE_ACCOUNT_TOKEN is set, the service-account API will not work
	unset OP_SERVICE_ACCOUNT_TOKEN && \
		write_permission=$([[ "{{WRITE_PERMISSION}}" == "true" ]] && echo ",write_items" || echo "") && \
		op service-account create {{PROJECT_NAME}}-{{CONTEXT}} \
				--expires-in '90d' \
				--vault "${OP_VAULT_UID}:read_items${write_permission}" \
				--raw

# generate r+w 1p service account token for terraform and other tools which can create 1P records
secrets_write-service-token: _not_production
	@echo '{{ BLUE }}Update your "env/all.local.sh" with this value:{{ NORMAL }}'

	just _secrets_service-token write true | jq -r -R '@sh "export OP_SERVICE_ACCOUNT_TOKEN=\(.)"'

# generate service account token for local development
[script]
secrets_local-service-token user=`whoami`: _not_production
	# @sh ensures the output is a valid bash export statement
	# the `$() || {}` is sneaky syntax that let's us exit if the subshell command fails
	token_shell_export=$(
		just _secrets_service-token {{user}} |
		jq -r -R '@sh "export OP_SERVICE_ACCOUNT_TOKEN=\(.)"'
	) || {
		echo "{{RED}}error: failed to generate 1Password service account token{{NORMAL}}" >&2
		exit 1
	}

	echo '{{ BLUE }}Update your "env/all.local.sh" OP_SERVICE_ACCOUNT_TOKEN with this value:{{ NORMAL }}'
	echo "$token_shell_export"

	if [ -f env/all.local.sh ]; then
		sed -i.bak "s|^export OP_SERVICE_ACCOUNT_TOKEN.*$|${token_shell_export}|" env/all.local.sh && rm env/all.local.sh.bak
		echo "{{GREEN}}Updated OP_SERVICE_ACCOUNT_TOKEN in env/all.local.sh{{NORMAL}}"
	fi

# grant GH actions access to the 1p vault, this needs to be done every 90d
secrets_ci_grant-github-actions: _not_production
	# 90d is the max expiration time allowed
	# this can be safely run multiple times, it will not regenerate the service account token
	service_account_token=$(just _secrets_service-token github-actions) && \
		gh secret set OP_SERVICE_ACCOUNT_TOKEN --app actions --body "$service_account_token"

# manage the op service account from the web ui
secrets_ci_manage: _not_production
	# https://$OP_ACCOUNT.1password.com/developer-tools/active/service-accounts
	# you cannot revoke/delete a service account with the cli, you must login and delete it from the web ui
	open https://$OP_ACCOUNT/developer-tools/directory
