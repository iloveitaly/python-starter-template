GITHUB_PROTECT_MASTER_RULESET := """
{
	"name": "Protect master from force pushes",
	"target": "branch",
	"enforcement": "active",
	"conditions": {
		"ref_name": {
			"include": ["refs/heads/master"],
			"exclude": []
		}
	},
	"rules": [
		{
			"type": "non_fast_forward"
		}
	]
}
"""

_github_repo:
	gh repo view --json nameWithOwner -q .nameWithOwner

# TODO this only supports deleting the single ruleset specified above
github_ruleset_protect_master_delete:
	repo=$(just _github_repo) && \
	  ruleset_name=$(echo '{{GITHUB_PROTECT_MASTER_RULESET}}' | jq -r .name) && \
		ruleset_id=$(gh api repos/$repo/rulesets --jq ".[] | select(.name == \"$ruleset_name\") | .id") && \
		(([ -n "${ruleset_id}" ] || (echo "No ruleset found" && exit 0)) || gh api --method DELETE repos/$repo/rulesets/$ruleset_id)

# adds github ruleset to prevent --force and other destructive actions on the github main branch
github_ruleset_protect_master_create: github_ruleset_protect_master_delete
	gh api --method POST repos/$(just _github_repo)/rulesets --input - <<< '{{GITHUB_PROTECT_MASTER_RULESET}}'

# Set GitHub Actions permissions for the repository to allow workflows to write and approve PR reviews
# This enables release-please to run without a personal access token
github_repo_permissions_create:
	repo_path=$(gh repo view --json nameWithOwner --jq '.nameWithOwner') && \
	gh api --method PUT "/repos/${repo_path}/actions/permissions/workflow" \
		-f default_workflow_permissions=write \
		-F can_approve_pull_request_reviews=true && \
	gh api "/repos/${repo_path}/actions/permissions/workflow"

github_repo_set_metadata:
	gh repo edit \
		--description "$(yq -r '.project.description // ""' pyproject.toml)" \
		--homepage "$(yq -r '.project.urls.Repository // ""' pyproject.toml)" \
		--add-topic "$(yq -r '.project.keywords // [] | join(",")' pyproject.toml)"

# set publish permissions, update metadata, and protect master; all in one command
github_setup: github_repo_permissions_create github_repo_set_metadata github_ruleset_protect_master_create
