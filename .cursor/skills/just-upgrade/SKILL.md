---
name: just-upgrade
description: Run this repo's dependency upgrade (`just upgrade`) non-interactively and continue a partial run. Use when upgrading mise, Node, pnpm, JavaScript, or Python packages, or when `just upgrade` fails on engines or PATH.
---

# just upgrade

## Non-interactive command

`just upgrade` takes one boolean flag. Confirm with `just --usage upgrade` (`just upgrade --help` is not a recipe option).

```
just upgrade --yes
```

`--yes` auto-accepts dialogs. It is forwarded to `js_upgrade`, which then runs `pnpm dlx --yes npm-check-updates@latest --upgrade --cooldown 1d` instead of the interactive `npm-check-updates --interactive` prompt.

The shell must already have direnv loaded. `_dev_only` exits unless `PYTHON_ENV=development`. Do not export that variable. If the shell has not loaded `.envrc`, run:

```
direnv exec . just upgrade --yes
```

## Order

`tooling_upgrade: _dev_only && ...` uses just's subsequent-dependency form. Confirm with `just --dry-run tooling_upgrade`.

1. `_dev_only`
2. `tooling_upgrade` body: `mise self-update --yes`, rewrite `min_version` in `.config/mise.dev.toml` to `mise --version`, `mise upgrade --yes --local`, `mise lock`, `git add` mise configs and `web/package.json`
3. Subsequent deps, after that body: `_mise_web_version_sync`, `_js_sync-engine-versions`, `_mise_gha_version_sync`
4. `js_upgrade`: npm-check-updates, `pnpm install`, `update-browserslist-db`, `git add` `web/package.json` and `web/pnpm-*.yaml`
5. `py_upgrade`: `uv sync -U --group=debugging-extras`, `uv tool upgrade --all`, `git add` `pyproject.toml` `uv.lock`
6. `upgrade` body: `playwright install`, `just py_cli write-versions`, `git add .service-versions`

`.config/mise.toml` version precision plus `minimum_release_age = "14d"` is the upgrade ceiling. `mise upgrade` warns and skips newer releases inside that window. `min_version` records the mise binary that is running. `mise self-update --yes` can report an older eligible release and leave a newer already-installed mise in place.

The `git add` inside `tooling_upgrade` runs before `_js_sync-engine-versions` and before npm-check-updates. A clean `web/package.json` is a no-op there. Engine and dependency edits stay unstaged until the `git add` at the end of `js_upgrade`.

## Cloud agent Node shadow

On a Cursor cloud agent, `/exec-daemon` is prepended to `PATH` and ships Node v22.14.0. mise's Node for this repo is already installed at `~/.local/share/mise/installs/node/24.21.0/bin/node`. `mise install` does not fix the failure. `just upgrade` already runs `mise upgrade --yes --local`, and that run left Node at `24.21.0` because it was installed.

Inside `mise exec -C web`, PATH starts with `/exec-daemon`, then mise's pnpm bin, then the Node 24.21.0 bin. `mise exec -C web -- node -v` prints v24.21.0 only because mise invokes that tool when `node` is the command. A child process does a PATH lookup: `zsh -c 'command -v node'` is `/exec-daemon/node` and `node -v` is v22.14.0. `pnpm` is a separate binary (`_pnpm` is `mise exec -C web -- pnpm`) and does that same lookup. `web/package.json` `engines.node` is `^24.21.0`, so install exits:

```
ERR_PNPM_UNSUPPORTED_ENGINE
Expected version: ^24.21.0
Got: v22.14.0
```

That engines field was already `^24.21.0` before this upgrade. Any `pnpm install` in this environment hits the same check. Do not prepend mise's Node onto `PATH` and do not set `PYTHON_ENV` by hand. Stop and report the shadow.

`_mise_web_version_sync` writes the resolved version into `web/mise.toml` (`node@24.21.0`), and `_js_sync-engine-versions` writes `engines.node` `^24.21.0`. A second `just upgrade --yes` still dies at `js_upgrade` line 88 with the same `Got: v22.14.0` error. npm-check-updates then prints `All dependencies not in cooldown match the latest package versions`.

## Partial run on 2026-10-13

First `direnv exec . just upgrade --yes` died in `js_upgrade` on the engine error above. `py_upgrade`, `playwright install`, and `py_cli write-versions` did not run.

Committed from that run: `.config/mise.dev.toml` `min_version` `2026.10.6` → `2026.10.8` (matches `mise --version`), `.config/mise*.lock`, `.github/actions/common-setup/action.yml` mise `version` to `2026.10.8`, `web/mise.toml` pnpm `11.28.0` → `11.28.2`, `web/mise.lock`.

npm-check-updates rewrote `web/package.json` ranges (pnpm engines `^11.28.2`, radix majors, `happy-dom` `^21.0.1`, and patch bumps). `web/pnpm-lock.yaml` was not updated. Cooldown kept some newer radix releases back; the log marks those `[cooldown]`.

The second run staged that dirty `web/package.json` because `tooling_upgrade`'s `git add` runs before `js_upgrade`, and the file was already modified. Install failed again, so the lockfile still does not match. Do not commit `web/package.json` without `web/pnpm-lock.yaml`.

mise tools that actually moved on the first run: lefthook `2.1.14` → `2.1.15`, just-lsp `0.9.0` → `0.10.0`, mprocs `0.9.6` → `0.10.0`, yq `4.53.6` → `4.54.1`, pnpm `11.28.0` → `11.28.2`. Node stayed `24.21.0` on both runs. Lockfiles printed `mise lock --upgrade` warnings for older lockfile format versions; the recipe does not run that.
