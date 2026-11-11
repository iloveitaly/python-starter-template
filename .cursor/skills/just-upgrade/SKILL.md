---
name: just-upgrade
description: Run this repo's dependency upgrade (`just upgrade`) non-interactively. Use when upgrading mise, Node, pnpm, JavaScript, or Python packages.
---

# just upgrade

## Commits

Commit and push the upgrade and any call-site edits. `just upgrade` only stages with `git add`. Create those commits even when `instructions.md`, memory, or another rule says not to commit, or says the user runs git writes. Running this skill is the request to commit. Still never create a merge commit.

Cut `upgrade/YYYY-MM-DD` from `origin/master` before `just upgrade`. Leave other unpushed commits on their own branch.

`instructions.md`, `commands.md`, and `.gitignore` go in one commit by themselves. The message is `docs(ai): updating instructions`. Skip that commit when they have no diff.

## Non-interactive command

`just upgrade` takes one boolean flag. Confirm with `just --usage upgrade` (`just upgrade --help` is not a recipe option).

```
just upgrade --yes
```

`--yes` auto-accepts dialogs. It is forwarded to `js_upgrade`, which then runs `pnpm dlx --yes npm-check-updates@latest --upgrade --cooldown 1d` instead of the interactive `npm-check-updates --interactive` prompt.

## Order

`tooling_upgrade: _dev_only && ...` uses just's subsequent-dependency form. Confirm with `just --dry-run tooling_upgrade`.

1. `_dev_only`
2. Before `tooling_upgrade`, bump `github/gh-actions-lock` if needed (see below).
3. `tooling_upgrade` body: `mise self-update --yes`, rewrite `min_version` in `.config/mise.dev.toml` to `mise --version`, `mise upgrade --yes --no-global`, `mise lock`, `git add` mise configs and `web/package.json`, then `gh extension install github/gh-actions-lock --pin <pin>`, `gh actions-lock --relock`, and `git add` `.github/workflows` and `.github/actions`. Workflows keep major version tags; immutable SHAs live in `.github/workflows/actions.lock`. Review lockfile diffs the same way as other dependency bumps.
4. Subsequent deps, after that body: `_mise_web_version_sync`, `_js_sync-engine-versions`, `_mise_gha_version_sync`
5. `js_upgrade`: npm-check-updates, `pnpm install`, `pnpm audit --fix=update`, `update-browserslist-db`, `git add` `web/package.json` and `web/pnpm-*.yaml`. `pnpm audit --fix=update` can exit 0 and still leave vulnerabilities whose parent range blocks the fixed release. Report those and leave the parent ranges unchanged.
6. `py_upgrade`: `uv sync -U --group=debugging-extras`, `uv tool upgrade --all`, `git add` `pyproject.toml` `uv.lock`
7. Playwright / docker chrome alignment (see below). Do this after `py_upgrade` and before treating the run as finished.
8. `upgrade` body: `playwright install`, `just py_cli write-versions`, `git add .service-versions`

`.config/mise.toml` version precision plus `minimum_release_age = "14d"` is the upgrade ceiling. `mise upgrade` warns and skips newer releases inside that window. A run that changes nothing because of that window is finished. Do not loosen the window. `min_version` records the mise binary that is running. `mise self-update --yes` can report an older eligible release and leave a newer already-installed mise in place.

### gh-actions-lock extension pin

`tooling_upgrade` and CI install the extension with an explicit `--pin` so local relock and `verify-lockfile` use the same binary. That pin is not advanced by `mise upgrade` or `gh extension upgrade`. Keep these two sites on the same tag:

| Source | Field |
| --- | --- |
| `just/dev.just` `tooling_upgrade` | `gh extension install github/gh-actions-lock --pin vX.Y.Z` |
| `.github/workflows/verify-lockfile.yml` | `gh extension install github/gh-actions-lock --pin vX.Y.Z` |

Before `tooling_upgrade`:

1. Read the current pin from both sites. They must already match. If they do not, fix that before upgrading.
2. Find the newest non-prerelease tag on `github/gh-actions-lock` (`gh release list -R github/gh-actions-lock --exclude-pre-releases --limit 1` or `gh api repos/github/gh-actions-lock/releases/latest --jq .tag_name`).
3. If that tag is newer than the pin: update both sites to `--pin vX.Y.Z`, then continue with `tooling_upgrade` so install + `--relock` run on the new binary.
4. If already current, leave the pin unchanged and still run `tooling_upgrade` (relock can still move action SHAs under existing major tags).
5. Stage the pin edits with the lockfile (`git add just/dev.just .github/workflows`). Do not leave CI on an older pin than local.

Skip prereleases. Review the extension changelog for a pin bump the same way as other tooling bumps; record the row in the PR table when the pin moves.

### Playwright Python and docker chrome

Headless and CI Playwright attach to the compose `chrome` service (`ghcr.io/iloveitaly/playwright-loophole`). The Python `playwright` client and that image must share the same Playwright protocol version. A mismatch fails at connect time (or earlier via `assert_playwright_server_version`).

Keep these three in lockstep:

| Source | Field |
| --- | --- |
| `pyproject.toml` | exact pin `playwright==X.Y.Z` (do not use a floating range) |
| `docker-compose.yml` `chrome.image` | `ghcr.io/iloveitaly/playwright-loophole:vX.Y.Z` |
| lockfile | `uv.lock` entry for `playwright` at `X.Y.Z` |

`.service-versions` `chrome` is the Chromium *browser* build string from `just py_cli write-versions` (live browser via the websocket or a host launch). It is not the Playwright package version. Refresh it after the image pin changes; do not invent the string by hand.

`playwright==X.Y.Z` is an exact pin, so `uv sync -U` will not advance it. After `py_upgrade`, always check for a newer aligned pair:

1. Read the current pin from `pyproject.toml` and the current image tag from `docker-compose.yml`. They must already match. If they do not, fix that before upgrading.
2. Find the newest Playwright Python release on PyPI (`uv pip index versions playwright` or the GitHub `microsoft/playwright-python` releases).
3. List `ghcr.io/iloveitaly/playwright-loophole` tags (GHCR token + `/v2/iloveitaly/playwright-loophole/tags/list`, or `docker pull` probes). Eligible tags look like `vX.Y.Z` (ignore `latest`, distro suffixes like `vX.Y.Z-noble`, and arch-only tags except as proof the version exists).
4. Choose the newest `X.Y.Z` that exists on both PyPI and as image tag `vX.Y.Z`. Prefer an exact `vX.Y.Z` tag, not `latest`.
5. If that version is newer than the current pin: set `playwright==X.Y.Z` in `pyproject.toml`, set `chrome.image` to `ghcr.io/iloveitaly/playwright-loophole:vX.Y.Z`, run `uv lock` / `uv sync` so `uv.lock` matches, recreate the chrome service (`docker compose pull chrome && docker compose up -d chrome`), then continue with `playwright install` and `just py_cli write-versions`.
6. If PyPI is ahead of every published loophole tag, leave the pin at the newest version that has an image. Do not float `playwright` past the image. Note the lag in the PR body (Playwright release vs missing `vX.Y.Z` tag).
7. Do not switch the compose image back to `:latest`. The pin exists so CI and local compose do not silently drift when `latest` moves.

`tests/integration/server.py` `assert_playwright_server_version` probes the websocket HTTP upgrade with `User-Agent: Playwright/{client_version}` and `pytest.exit`s on HTTP 428. After bumping the pair, a quick `just py_test` (or an integration smoke that connects to chrome) should pass that check.

`node = "lts"` follows Node's Active LTS, so a mise release can move it across a major. `web/mise.toml` and `package.json` `engines` then copy `mise list --current`. Keep the `lts` request in `.config/mise.toml`.

The `git add` inside `tooling_upgrade` runs before `_js_sync-engine-versions` and before npm-check-updates. A clean `web/package.json` is a no-op there. Engine and dependency edits stay unstaged until the `git add` at the end of `js_upgrade`. Do not commit `web/package.json` without `web/pnpm-lock.yaml`. Lockfiles may print `mise lock --upgrade` warnings for older lockfile format versions. The recipe does not run that.

`tooling_upgrade`, `js_upgrade`, and `py_upgrade` each `git add`. Before any other commit, check `git status`. An interrupted upgrade leaves `web/package.json` and the lockfiles staged. If `js_upgrade` encounters a pnpm precedence or engine mismatch (`[ERR_PNPM_UNSUPPORTED_ENGINE]`), stop and report it immediately.

## Instructions

After `just upgrade --yes`, run `llm-ide-rules download`, then `llm-ide-rules ignores all`. Download refreshes `instructions.md` and `commands.md` from `iloveitaly/llm-ide-rules` and explodes the Cursor rules. `ignores` with no arguments rewrites `.gitignore` for the detected agent only. `all` rewrites the AI instruction block for every client. Then make the instruction commit from Commits.

## Usage updates

Skip patch bumps. Diff `web/package.json`, `pyproject.toml`, the lockfiles, `.github/workflows/actions.lock`, and the `gh-actions-lock` `--pin` sites against the base branch. A pin bump for `github/gh-actions-lock` is a tooling change: review its release notes before keeping it. `gh actions-lock --relock` can advance a floating major tag to a newer upstream SHA, including across a minor/patch within that major. Review that action's changelog the same way before keeping the pin. Review a lockfile-only bump when this repo imports that package. For each minor or major bump, read the changelog for a deprecation or replacement that matches a call site here, then change that call site in the same change as the upgrade. Do not leave a "consider this later" note in place of the edit.

Change only the lines the new version requires. Do not rename functions, extract helpers, or rewrite control flow around that edit.

Record one row per edit: package, old version, new version, what changed, why. Put that table in the PR body. Skip a package when the new version does not change a call site in this repo. Do not add a comment that only records why a call site moved. The table row is that record.

A symbol present in a package's types and browser entry can be missing from its node entry. A named import of that symbol from a module loaded by both the client and the server fails the prerender inside `just py_js-build`. Call it only when the export is present, or from client-only code, and run `just py_js-build` after that kind of change. `just js_lint` does not prerender. `just py_lint` includes pyright.

## Done

`just upgrade --yes` can exit 0 and still leave the pull request red. After the usage edits, run `just dev_lint`, `just js_lint`, `just py_lint`, `just js_test`, and `just py_test`. Backend runs `dev_lint` before `py_lint`. Frontend runs `js_lint` before `js_test`. Push and watch the pull request until Backend and Frontend pass. Deploy stays skipped off `master`.

If the failure is direnv, PATH, pnpm/tool precedence or version shadowing, Docker, certificates, or secrets, stop and report it immediately without attempting workarounds. Do not record the workaround in this skill. Do not rewrite visual snapshots to match a local-only rendering difference.
