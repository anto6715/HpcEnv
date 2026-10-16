# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

Personal dotfiles + HPC tooling for the user's account on the CMCC supercomputer (hostname `juno`, scheduler is IBM **LSF**, auth is **Kerberos**). It deploys shell/editor config via symlinks and ships standalone shell/Python utilities for ocean-modeling workflows (NEMO/Cylc runs, CMEMS data delivery, core-hour accounting).

There is no build system and no test suite — utilities are run directly. Changes are validated by running the script, not by a test runner.

## Setup commands

```bash
# Install the full toolchain (rust, go, uv, ruff, ty, helix, node, shellcheck, language servers, lazygit)
scripts/prerequisites.sh

# Deploy / remove the dotfile symlinks defined in symlinks.conf
scripts/symlinks.sh --create
scripts/symlinks.sh --delete [--include-files]
```

`symlinks.conf` maps `source:target` pairs (one per line, `$(pwd)`-relative sources). Wildcard sources like `bin/*` link each matched file into the target directory. `scripts/symlinks.sh` evals these lines, so editing the deployment means editing `symlinks.conf`, not the script.

## Linting / formatting

- **Python**: `ruff` — config in `ruff/ruff.toml` (target py312, line-length 120, `E`/`F`/`I` lint rules, double-quote format). Type checking via `ty`. The `lib/.venv` is a uv-managed venv (Jupyter stack) and is not the project's dependency manifest.
- **Shell**: `shellcheck`; bash language server for the editor.
- Both ruff and the venv are gitignored where generated (`__pycache__`, `*.pyc`, `package.json`/`package-lock.json`).

## Layout

- `bash/` — shell config, symlinked into `$HOME` and `$HOME/.config/bash/`. `.bashrc` sources `aliases.bash` + `custom.bash`; `custom.bash` builds PATH and tool env (rust/go/nvm/kerberos/helix); `yabpc.bash` is the custom prompt (`PROMPT_COMMAND=yabpc`). Behavior branches on `$HPC_SYSTEM` (e.g. `juno`).
- `bin/` — user commands symlinked into `$HOME/.local/bin`. LSF helpers (`tail-lsf-job`, `bkill-all`), and `.exp` Expect scripts (`kerb`, `vpn`, `juno`) automating interactive Kerberos/VPN/SSH login. `git-wt` runs as `git wt init <url> <dir> [<branch>[:<folder>]]...`: a worktree container (bare clone in `<dir>/.bare`, `<dir>/.git` pointing to it, fetch refspec for all remote branches, one worktree per branch with its upstream set, then `clean-branches`); `git wt clean-branches [-n] <dir>` removes the local branches a bare clone copies from the remote when they are not checked out and still equal `origin/<branch>` (via `update-ref -d <ref> <old>`), so `git worktree add <folder> <branch>` tracks `origin/<branch>`; `-n` prints/lists only. `vault-snapshot` (laptop only) commits the user's own edits in the Obsidian vault `~/Obsidian/CMCC` as `User notes: auto-snapshot` and pushes it to `origin` (private GitLab); it skips a turn while git is busy or a file to commit (outside `.obsidian/`) changed in the last `QUIET_MIN` minutes, never commits `.obsidian/graph.json` (pathspec exclude) or the workspace files (the vault's `.gitignore`; an exclude naming an ignored path makes `git add` exit 1), `-n` is a dry run.
- `systemd/` — systemd user units symlinked into `$HOME/.config/systemd/user` (`systemd/*` in `symlinks.conf`; enable them by hand with `systemctl --user enable --now <unit>`). `vault-snapshot.timer` runs `vault-snapshot.service` (→ `bin/vault-snapshot`) hourly, `Persistent=true`; the service never prompts for a passphrase (`GIT_TERMINAL_PROMPT=0`, `SSH_ASKPASS_REQUIRE=never`), so a push without the key in the agent fails and the next run retries.
- `lib/` — domain scripts run in place (NOT symlinked). Ocean-model run management around Cylc/NEMO (`*_lobc*`, `*_hst_sla*`, `check_run.py`), netCDF processing (`extract_nc_var.py`, `daily_mean.py`, `min_max4.py`), and accounting (`calc_core_hour.sh`, which reads `/users_home/.accounting/...` CSVs).
- `scripts/` — repo maintenance: `prerequisites.sh`, `symlinks.sh`, `generate_delivery_xml*.py` (CMEMS product delivery manifests), `check_my_timeseries.py` (MY timeseries check on MDS), `prepare_dv_upload.py` (MDS DV test upload of MEDSEA ANFC 202611: one folder per dataset, two files each; dataset map embedded), `clean_longrun.py` (removes `nemo_ww/*out_*`, `nemo_ww/*1ts*`, `oceanvar/corr*` from the `<root>/YYYYMMDD` day folders of a longrun in a date range; dry-run unless `--apply`), `clean_blk_restarts.py` (BLK/BSFS EAS9 longrun: removes the restarts of a date range from `restart/YYYYMMDDT2400` and from the `YYYYMMDD/analysis` Cylc work dir, keeping month-ends and the last N days; counts hard links to report the space really freed; dry-run unless `--apply`), and `utils.sh`.
- `helix/`, `wezterm/`, `ruff/` — editor/tool config dirs, symlinked whole into `$HOME/.config/`.
- `templates/` — starter files for new scripts (`bash.sh`, `bash_getopt.sh`, `python_click.py`, `python_argparse.py`). Use these as the starting point when adding a new utility.

## Conventions

- **`scripts/utils.sh` provides the logging primitives** (`info`/`success`/`warning`/`error`, colored via `tput`). Bash scripts source it (`. "$SCRIPT_DIR/utils.sh"`) rather than re-implementing colored output. It also save/restores `xtrace`.
- Scripts resolve their own location with `SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"` and guard "run directly vs sourced" with `if [ "$(basename "$0")" = "$(basename "${BASH_SOURCE[0]}")" ]`. Follow this pattern so functions stay sourceable.
- HPC-specific paths and hostnames (`/work/cmcc/$USER`, `/users_home/.accounting`, `juno`, LSF `bjobs`/`bkill`, `$HOME/.lsbatch`) are hardcoded on purpose — they reflect the target cluster, not placeholders.
