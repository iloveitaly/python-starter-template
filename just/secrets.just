#######################
# Secrets (via 1Password)
#######################

_secrets_service-token CONTEXT WRITE_PERMISSION="false":
	# if OP_SERVICE_ACCOUNT_TOKEN is set, the service-account API will not work
	unset OP_SERVICE_ACCOUNT_TOKEN && \
	write_permission=$([[ "{{WRITE_PERMISSION}}" == "true" ]] && echo ",write_items" || echo "") && \
	op service-account create {{PROJECT_NAME}}-{{CONTEXT}} \
			--expires-in '90d' \
			--vault "${OP_VAULT_UID}:read_items${write_permission}" \
			--raw

# for terraform and other tools which can create entries
secrets_write-service-token: _dev_only
	@echo '{{ BLUE }}Update your ".env.local" with this value:{{ NORMAL }}'

	just _secrets_service-token write true | jq -r -R '@sh "export OP_SERVICE_ACCOUNT_TOKEN=\(.)"'

# generate service account token for local development
secrets_local-service-token user=`whoami`: _dev_only
	just _secrets_service-token {{user}} | jq -r -R '@sh "export OP_SERVICE_ACCOUNT_TOKEN=\(.)"'

# grant GH actions access to the 1p vault, this needs to be done every 90d
secrets_ci_grant-github-actions: _dev_only
	# 90d is the max expiration time allowed
	# this can be safely run multiple times, it will not regenerate the service account token
	service_account_token=$(just _secrets_service-token github-actions) && \
		gh secret set OP_SERVICE_ACCOUNT_TOKEN --app actions --body "$service_account_token"

# manage the op service account from the web ui
secrets_ci_manage: _dev_only
	# you cannot revoke/delete a service account with the cli, you must login and delete it from the web ui
	open https://$OP_ACCOUNT/developer-tools/directory
