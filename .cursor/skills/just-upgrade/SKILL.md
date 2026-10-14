---
name: just-upgrade
description: Run this repo's dependency upgrade (`just upgrade`) non-interactively and continue a partial run. Use when upgrading mise, Node, pnpm, JavaScript, or Python packages.
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

`.config/mise.toml` version precision plus `minimum_release_age = "14d"` is the upgrade ceiling. `mise upgrade` warns and skips newer releases inside that window. `min_version` records the mise binary that is running. `mise self-update --yes` can report an older eligible release and leave a newer already-installed mise in place.

The `git add` inside `tooling_upgrade` runs before `_js_sync-engine-versions` and before npm-check-updates. A clean `web/package.json` is a no-op there. Engine and dependency edits stay unstaged until the `git add` at the end of `js_upgrade`. Do not commit `web/package.json` without `web/pnpm-lock.yaml`. Lockfiles may print `mise lock --upgrade` warnings for older lockfile format versions. The recipe does not run that.
