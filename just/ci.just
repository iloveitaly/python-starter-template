#######################
# CI Management
#######################

GHA_YML_NAME := "build_and_publish.yml"

# TODO should we scope these requests via `--branch "$(git branch --show-current)"`

_gha_running_run_id:
	gh run list --status=in_progress --workflow={{GHA_YML_NAME}} --json databaseId --jq '.[0].databaseId'

_gha_last_failed_run_id:
	# NOTE this is tied to the name of the yml!
	branch=$(git branch --show-current) && \
		gh run list --branch "$branch" --status=failure --workflow={{GHA_YML_NAME}} \
		--json databaseId --jq '.[0].databaseId'

# rerun last failed CI run
ci_rerun:
	# TODO should scope to the current users runs?
	gh run rerun $(just _gha_last_failed_run_id)

# view the last failed gha in the browser
ci_last_failed-view:
	gh run view --web $(just _gha_last_failed_run_id)

# tail failed logs right in your terminal
ci_last_failed-tail:
	# TODO output here is still messy, may be able to customize with --template
	gh run view --log-failed $(just _gha_last_failed_run_id)

# download test-results artifact from last failed gha run
[arg("output-dir", long, help="output the raw downloaded directory", value="true")]
[script]
ci_last_failed-download output-dir="false":
	downloaded_test_results_directory="$TMP_DIRECTORY/gha-artifacts"
	mkdir -p "$downloaded_test_results_directory"

	failed_run_id=$(just _gha_last_failed_run_id)

	# helpful to download to unique folder for two reasons:
	#   1. easier to match up to web GHA view
	#   2. eliminates risk of gh-cli erroring out bc the directory already exists
	failed_run_target_directory="${downloaded_test_results_directory}/${failed_run_id}"
	rm -rf "$failed_run_target_directory"

	# the structure of the downloaded files here is tricky and dependent on the input paths (whether they exist or not)
	# `tmp/gha-artifacts/21836083821/tmp/test-results/` is the dir-path you most likely want
	# `--name` is required in order for the name of test artifact not to be included in the path
	gh run download --dir "$failed_run_target_directory" --name test-results $failed_run_id

	if [[ "{{output-dir}}" == "true" ]]; then
		echo "${failed_run_target_directory}"
	else
		echo "{{BLUE}}Downloaded artifacts to ${failed_run_target_directory}{{NORMAL}}"
	fi

# cancel all currently running CI jobs
ci_running-cancel:
	gh run list --status in_progress --json databaseId -q '.[].databaseId' | xargs -n1 gh run cancel

# live tail currently running ci job
ci_watch-running *flag:
	if {{ if flag == "--web" { "true" } else { "false" } }}; then \
		gh run view --web $(just _gha_running_run_id); \
	else \
		gh run watch $(just _gha_running_run_id); \
	fi

# very destructive action: deletes all workflow run logs, useful for cleaning up sensitive data leaks
[confirm('Are you sure you want to delete all workflow logs?')]
ci_wipe_run_logs:
	REPO=$(gh repo view --json name --jq '.name') && \
	OWNER=$(gh repo view --json owner --jq '.owner.login') && \
		gh api repos/$OWNER/$REPO/actions/workflows --paginate --jq '.workflows[] | .id' | \
		xargs -I{} gh api repos/$OWNER/$REPO/actions/workflows/{}/runs --paginate --jq '.workflow_runs[].id' | \
			xargs -I{} gh api -X DELETE /repos/$OWNER/$REPO/actions/runs/{}
