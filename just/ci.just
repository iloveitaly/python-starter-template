#######################
# CI Management
#######################

GHA_YML_NAME := "build_and_publish.yml"

# TODO should scope to the current users runs
# rerun last failed CI run
ci_rerun:
	gh run rerun $(just _gha_last_failed_run_id)

# view the last failed gha in the browser
ci_view-last-failed:
	gh run view --web $(just _gha_last_failed_run_id)

# TODO output here is still messy, may be able to customize with --template
# tail failed logs right in your terminal
ci_tail-last-failed:
	gh run view --log-failed $(just _gha_last_failed_run_id)

# live tail currently running ci job
ci_watch-running *flag:
	if {{ if flag == "--web" { "true" } else { "false" } }}; then \
		gh run view --web $(just _gha_running_run_id); \
	else \
		gh run watch $(just _gha_running_run_id); \
	fi

# very destructive action: deletes all workflow run logs
[confirm('Are you sure you want to delete all workflow logs?')]
ci_wipe_run_logs:
	REPO=$(gh repo view --json name --jq '.name') && \
	OWNER=$(gh repo view --json owner --jq '.owner.login') && \
		gh api repos/$OWNER/$REPO/actions/workflows --paginate --jq '.workflows[] | .id' | \
		xargs -I{} gh api repos/$OWNER/$REPO/actions/workflows/{}/runs --paginate --jq '.workflow_runs[].id' | \
			xargs -I{} gh api -X DELETE /repos/$OWNER/$REPO/actions/runs/{}

# get the last failed run ID
_gha_last_failed_run_id:
	# NOTE this is tied to the name of the yml!
	gh run list --status=failure --workflow={{GHA_YML_NAME}} --json databaseId --jq '.[0].databaseId'

_gha_running_run_id:
	gh run list --status=in_progress --workflow={{GHA_YML_NAME}} --json databaseId --jq '.[0].databaseId'