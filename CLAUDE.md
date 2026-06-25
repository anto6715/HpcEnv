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
- `bin/` — user commands symlinked into `$HOME/.local/bin`. LSF helpers (`tail-lsf-job`, `bkill-all`), and `.exp` Expect scripts (`kerb`, `vpn`, `juno`) automating interactive Kerberos/VPN/SSH login.
- `lib/` — domain scripts run in place (NOT symlinked). Ocean-model run management around Cylc/NEMO (`*_lobc*`, `*_hst_sla*`, `check_run.py`), netCDF processing (`extract_nc_var.py`, `daily_mean.py`, `min_max4.py`), and accounting (`calc_core_hour.sh`, which reads `/users_home/.accounting/...` CSVs).
- `scripts/` — repo maintenance: `prerequisites.sh`, `symlinks.sh`, `generate_delivery_xml*.py` (CMEMS product delivery manifests), and `utils.sh`.
- `helix/`, `wezterm/`, `ruff/` — editor/tool config dirs, symlinked whole into `$HOME/.config/`.
- `templates/` — starter files for new scripts (`bash.sh`, `bash_getopt.sh`, `python_click.py`, `python_argparse.py`). Use these as the starting point when adding a new utility.

## Conventions

- **`scripts/utils.sh` provides the logging primitives** (`info`/`success`/`warning`/`error`, colored via `tput`). Bash scripts source it (`. "$SCRIPT_DIR/utils.sh"`) rather than re-implementing colored output. It also save/restores `xtrace`.
- Scripts resolve their own location with `SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"` and guard "run directly vs sourced" with `if [ "$(basename "$0")" = "$(basename "${BASH_SOURCE[0]}")" ]`. Follow this pattern so functions stay sourceable.
- HPC-specific paths and hostnames (`/work/cmcc/$USER`, `/users_home/.accounting`, `juno`, LSF `bjobs`/`bkill`, `$HOME/.lsbatch`) are hardcoded on purpose — they reflect the target cluster, not placeholders.
