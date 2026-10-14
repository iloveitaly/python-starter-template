---
name: just-upgrade
description: Run this repo's dependency upgrade (`just upgrade`) non-interactively, apply minor and major call-site updates, and finish when CI is green. Use when upgrading mise, Node, pnpm, JavaScript, or Python packages.
---

# just upgrade

## Non-interactive command

`just upgrade` takes one boolean flag. Confirm with `just --usage upgrade` (`just upgrade --help` is not a recipe option).

```
just upgrade --yes
```

`--yes` auto-accepts dialogs. It is forwarded to `js_upgrade`, which then runs `pnpm dlx --yes npm-check-updates@latest --upgrade --cooldown 1d` instead of the interactive `npm-check-updates --interactive` prompt.

## Order

`tooling_upgrade: _dev_only && ...` uses just's subsequent-dependency form. Confirm with `just --dry-run tooling_upgrade`.

1. `_dev_only`
2. `tooling_upgrade` body: `mise self-update --yes`, rewrite `min_version` in `.config/mise.dev.toml` to `mise --version`, `mise upgrade --yes --local`, `mise lock`, `git add` mise configs and `web/package.json`
3. Subsequent deps, after that body: `_mise_web_version_sync`, `_js_sync-engine-versions`, `_mise_gha_version_sync`
4. `js_upgrade`: npm-check-updates, `pnpm install`, `update-browserslist-db`, `git add` `web/package.json` and `web/pnpm-*.yaml`
5. `py_upgrade`: `uv sync -U --group=debugging-extras`, `uv tool upgrade --all`, `git add` `pyproject.toml` `uv.lock`
6. `upgrade` body: `playwright install`, `just py_cli write-versions`, `git add .service-versions`

`.config/mise.toml` version precision plus `minimum_release_age = "14d"` is the upgrade ceiling. `mise upgrade` warns and skips newer releases inside that window. A run that changes nothing because of that window is finished. Do not loosen the window. `min_version` records the mise binary that is running. `mise self-update --yes` can report an older eligible release and leave a newer already-installed mise in place.

The `git add` inside `tooling_upgrade` runs before `_js_sync-engine-versions` and before npm-check-updates. A clean `web/package.json` is a no-op there. Engine and dependency edits stay unstaged until the `git add` at the end of `js_upgrade`. Do not commit `web/package.json` without `web/pnpm-lock.yaml`. Lockfiles may print `mise lock --upgrade` warnings for older lockfile format versions. The recipe does not run that.

`tooling_upgrade`, `js_upgrade`, and `py_upgrade` each `git add`. Before any other commit, check `git status`. An interrupted upgrade leaves `web/package.json` and the lockfiles staged.

## Usage updates

Skip patch bumps. Diff `web/package.json`, `pyproject.toml`, and the lockfiles against the base branch. Review a lockfile-only bump when this repo imports that package. For each minor or major bump, read the changelog for a deprecation or replacement that matches a call site here, then change that call site in the same change as the upgrade. Do not leave a "consider this later" note in place of the edit.

Record one row per edit: package, old version, new version, what changed, why. Put that table in the PR body. Skip a package when the new version does not change a call site in this repo.

A symbol present in a package's types and browser entry can be missing from its node entry. A named import of that symbol from a module loaded by both the client and the server fails the prerender inside `just py_js-build`. Call it only when the export is present, or from client-only code, and run `just py_js-build` after that kind of change. `just js_lint` does not prerender. `just py_lint` includes pyright.

## Done

`just upgrade --yes` can exit 0 and still leave the pull request red. After the usage edits, run `just js_lint`, `just py_lint`, `just js_test`, and `just py_test`. Push and watch the pull request until Backend and Frontend pass. Deploy stays skipped off `master`.

If the failure is direnv, PATH, Docker, certificates, or secrets, stop and report it. Do not record the workaround in this skill. Do not rewrite visual snapshots to match a local-only rendering difference.
