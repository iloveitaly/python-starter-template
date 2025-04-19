#######################
# GitHub
#######################

GITHUB_RULESET := """
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

github_ruleset_delete:
	repo=$(just _github_repo) && \
	  ruleset_name=$(echo '{{GITHUB_RULESET}}' | jq -r .name) && \
		ruleset_id=$(gh api repos/$repo/rulesets --jq ".[] | select(.name == \"$ruleset_name\") | .id") && \
		(([ -n "${ruleset_id}" ] || (echo "No ruleset found" && exit 0)) || gh api --method DELETE repos/$repo/rulesets/$ruleset_id)

# prevent --force and other destructive actions on the github repo
github_ruleset: github_ruleset_delete
	gh api --method POST repos/$(just _github_repo)/rulesets --input - <<< '{{GITHUB_RULESET}}'
