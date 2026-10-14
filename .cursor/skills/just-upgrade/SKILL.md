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

Run that command directly. Do not prefix it with `direnv exec`.

`_dev_only` exits unless `PYTHON_ENV=development`. Do not export that variable. A normal interactive zsh loads it through the direnv hook in `~/.zshrc` (`eval "$(direnv hook zsh)"`). Agent commands run as non-interactive, non-login `/bin/zsh -c` (`interactive` off, no `-l`, argv0 `/bin/zsh`). That invocation reads `~/.zshenv` only. `.zshrc` is interactive-only, and there is no `~/.zprofile` sourcing it, so the hook never runs and `PYTHON_ENV` stays unset. A bare `just upgrade --yes` then fails immediately:

```
error: PYTHON_ENV must be set to 'development'
error: recipe `_dev_only` failed on line 19 with exit code 1
```

`~/.zshenv` only exports `MISE_ENV` and `OP_INTEGRATION_DISABLED`. The direnv hook is not there. `just` itself runs `zsh -ceuB`, which inherits the parent environment and also skips `~/.zshrc`.

`direnv hook zsh` only registers `precmd` and `chpwd`. Upstream `internal/cmd/shell_zsh.go` returns immediately when the shell is not interactive or when zsh's read-only `$ZSH_SUBSHELL` is not 0 (`[[ ! -o interactive || $ZSH_SUBSHELL -ne 0 ]]`). That guard is not in installed direnv 2.37.1. A non-interactive shell still never runs `precmd`, so the hook does not load `.envrc`. Copying it into `~/.zshenv` does not help `zsh -c`. Non-interactive injection is `direnv export zsh` (eval the diff) or `direnv exec DIR COMMAND`. `eval "$(direnv export zsh)"` does load it. With `OP_INTEGRATION_DISABLED` already exported, a `ZDOTDIR` whose `.zshenv` runs that export makes `zsh -ceuB` print `PYTHON_ENV=development` in `/workspace` and leaves it unset in `/tmp`. `direnv export zsh` took about 0.08s here.

zsh has no startup file that only non-interactive, non-login shells read. Those shells read `/etc/zshenv` and `~/.zshenv`, and every other zsh reads those too. In [agent-containers](https://github.com/iloveitaly/agent-containers) `cursor/install.sh`, append this to the ubuntu user's `~/.zshenv` after the `OP_INTEGRATION_DISABLED` and `MISE_ENV` lines. Keep the existing `direnv hook` in `~/.zshrc` for interactive `cd`.

```zsh
# zsh -c and just's zsh -ceuB are non-interactive and non-login. They never source .zshrc.
# .zshenv also runs for interactive and login shells, so the option check limits this to those two.
if [[ ! -o interactive && ! -o login && -z "${DIRENV_DIR:-}" ]] && command -v direnv >/dev/null 2>&1; then
  eval "$(direnv export zsh)"
fi
```

Checked with a temporary `ZDOTDIR`: `zsh -c` and `zsh -ceuB` match. `zsh -ic`, `zsh -lc`, and `zsh -lic` skip. At `.zshenv` time the login option still reflects the invocation. The agent command later restores `setopt login` from its snapshot, which is too late to change which startup files ran.

Write it even when direnv was already installed. The current script only appends the hook inside `if $need_direnv`, and only to `~/.zshrc`. Guard the append so a second install does not duplicate it. `.envrc` calling `just` before this export finishes can recurse, because `DIRENV_DIR` is not set until export returns. `env/host.sh` already exists in this checkout, so `.envrc` does not call `just dev_generate_hosts`.

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

## Fix

`mise install` does not help. Node 24.21.0 is already installed.

The exec daemon prepends its own directory at process start (`prependExecDaemonBundleToPath`, `dirname(process.execPath)` → `/exec-daemon`) so every child resolves the bundled `node` and `rg`. With `--origin-cli-enabled` it also prepends `/exec-daemon/tools`. That `node` is v22.14.0. `.venv/bin` is in the same prefix and has no `node`.

mise path mode keeps every `PATH` entry before the first mise-managed entry as a prefix. `/exec-daemon` is in that prefix, so `mise hook-env` and `mise exec` both emit it ahead of `.../node/24.21.0/bin`. Another precmd hook does not change this. `hook-env` is the rewrite that puts the prefix back. `just` runs `zsh -ceuB`, which does not source `.zshrc`, so an interactive `mise activate` hook never runs for `just upgrade`.

`mise activate --shims` puts `~/.local/share/mise/shims` first and does not run that rewrite. When the shims directory is already ahead of `/exec-daemon`, `mise exec -C web` resolves `node` to `.../node/24.21.0/bin/node` and leaves `/exec-daemon` after the tool bins (node bin at position 3, `/exec-daemon` at 27). A shim at the front of `PATH` with no `mise exec` also prints v24.21.0.

This repo activates path mode (`bootstrap.sh` uses `mise activate` with no `--shims`). Shims have to be first in the environment `just` inherits, and a later path-mode `hook-env` must not run, or `/exec-daemon` moves back in front.

The docs name two ways to put tools on `PATH`, not a separate prepend mode. `mise activate` is PATH activation: it prepends each tool's `bin` directory and rewrites `PATH` on prompt and `cd`. `mise activate --shims` is shim mode: it prepends `~/.local/share/mise/shims` and does not rewrite `PATH` at each prompt. See [Shims](https://mise.jdx.dev/dev-tools/shims.html).

`activate_aggressive` is the PATH-activation setting, not a third mode. The docs say a `PATH=` line after `mise activate` in the shell rc wins unless this is true, or unless `mise activate` is last in that file. With it set, `mise hook-env` and `mise exec -C web` both place `.../node/24.21.0/bin` before `/exec-daemon`, and `node -v` is v24.21.0. `mise exec` reads it from the user config, so `just`'s non-interactive `zsh -ceuB` picks it up with no shell hook.

[agent-containers](https://github.com/iloveitaly/agent-containers) already writes that user config from `cursor/install.sh` to `~/.config/mise/config.toml` (`trusted_config_paths`, global `uv`). Add `activate_aggressive = true` under that `[settings]` table. `miserc.toml` is the wrong file: it is for values mise reads before config (`env`). Do not put this in the project's `.config/mise.toml`; that would change every developer's PATH, not only agent images. Leave `engines.node` in place. Do not turn off pnpm's engine check.

On 2026-10-13 that flag was set in this VM's `~/.config/mise/config.toml` only. `mise settings get activate_aggressive` was `true`, and `mise exec -C web` resolved `node` to `.../node/24.21.0/bin/node` with `/exec-daemon` at PATH position 26. `direnv exec . just upgrade --yes` then passed `js_upgrade` (`pnpm install` updated `web/pnpm-lock.yaml`) and `py_upgrade` (`uv sync -U` updated `uv.lock`). `playwright install` downloaded Firefox and WebKit and exited 0 after a host-deps warning (`sudo playwright install-deps`). The first `just py_cli write-versions` failed: `redis.workspace.orb.local:6379` did not resolve.

`direnv exec . just docker_up` starts postgres, redis, mailpit, and geoip, then on Linux runs `uvx docker-hosts@latest`. That tool's default `--tld` is `localhost`, so `/etc/hosts` gets `redis.localhost`, not `redis.workspace.orb.local`. This checkout's `SERVICES_HOST` is `workspace.orb.local` (`env/not_production.sh`). CI sets `REDIS_HOST=redis.localhost` instead. Re-running docker-hosts with `--tld workspace.orb.local` made `redis.workspace.orb.local` resolve to the container IP, and Redis answered `PONG`. The next `direnv exec . just upgrade --yes` exited 0. `write-versions` changed `.service-versions` python `3.14.6` → `3.14.7` and logged `python version mismatch expected=3.14.6 got=3.14.7` before that write. Playwright still printed the host-deps warning and did not fail the recipe.

`_mise_web_version_sync` writes the resolved version into `web/mise.toml` (`node@24.21.0`), and `_js_sync-engine-versions` writes `engines.node` `^24.21.0`. A second `just upgrade --yes` still dies at `js_upgrade` line 88 with the same `Got: v22.14.0` error. npm-check-updates then prints `All dependencies not in cooldown match the latest package versions`.

## Partial run on 2026-10-13

First `direnv exec . just upgrade --yes` died in `js_upgrade` on the engine error above. `py_upgrade`, `playwright install`, and `py_cli write-versions` did not run.

Committed from that run: `.config/mise.dev.toml` `min_version` `2026.10.6` → `2026.10.8` (matches `mise --version`), `.config/mise*.lock`, `.github/actions/common-setup/action.yml` mise `version` to `2026.10.8`, `web/mise.toml` pnpm `11.28.0` → `11.28.2`, `web/mise.lock`.

npm-check-updates rewrote `web/package.json` ranges (pnpm engines `^11.28.2`, radix majors, `happy-dom` `^21.0.1`, and patch bumps). `web/pnpm-lock.yaml` was not updated. Cooldown kept some newer radix releases back; the log marks those `[cooldown]`.

The second run staged that dirty `web/package.json` because `tooling_upgrade`'s `git add` runs before `js_upgrade`, and the file was already modified. Install failed again, so the lockfile still does not match. Do not commit `web/package.json` without `web/pnpm-lock.yaml`.

mise tools that actually moved on the first run: lefthook `2.1.14` → `2.1.15`, just-lsp `0.9.0` → `0.10.0`, mprocs `0.9.6` → `0.10.0`, yq `4.53.6` → `4.54.1`, pnpm `11.28.0` → `11.28.2`. Node stayed `24.21.0` on both runs. Lockfiles printed `mise lock --upgrade` warnings for older lockfile format versions; the recipe does not run that.
