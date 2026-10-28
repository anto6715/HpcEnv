# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

Personal dotfiles + HPC tooling, whose goal is to move smoothly from one machine to another: the user's laptop (Debian/Ubuntu) and their account on the CMCC supercomputer (hostname `juno`, scheduler is IBM **LSF**, auth is **Kerberos**, no sudo). It installs a user toolchain in `$HOME`, deploys shell/editor config via symlinks, and ships standalone shell/Python utilities for ocean-modeling workflows (NEMO/Cylc runs, CMEMS data delivery, core-hour accounting).

There is no build system and no test suite — utilities are run directly. Changes are validated by running the script, not by a test runner. Install/link changes can be tested without touching the real home with a throwaway `HOME=<dir> scripts/symlinks.sh --create`, or end to end in a clean `debian:stable` container (Docker is available on the laptop).

## Setup commands

```bash
./install.sh [--profile laptop|juno] [--check] [--backup]   # whole setup; --check reports only
scripts/prerequisites.sh [--check]                # user toolchain only (no root)
scripts/symlinks.sh --create [--profile P] [--backup]
scripts/symlinks.sh --delete [--include-files]
```

- `install.sh` runs: apt packages (laptop only, `APT_PACKAGES` array, via sudo) → `prerequisites.sh` → `symlinks.sh --create` (`--backup` passed through) → prints the manual steps (GPG/`pass` store, SSH, Kerberos realm, non-apt apps, systemd timer). Exit 1 if any step failed.
- Profile: `detect_profile` in `scripts/utils.sh` returns `juno` when `HPC_SYSTEM=juno` or the hostname contains `juno`, else `laptop`.
- `prerequisites.sh` is a list of `ensure <probe> "<desc>" <cmd...>` lines in `main()`: `<probe>` is a binary on PATH or a path to an executable; skipped when present. It calls `activate` (puts `~/.local/bin`, cargo, go, nvm, Miniforge on PATH) at start and after each install, because the script never reads `~/.bashrc`. A missing package manager makes its tools "skipped", and a summary lists failures. Installers must not edit rc files (`~/.bashrc` links into this repo): rustup `--no-modify-path`, uv `UV_NO_MODIFY_PATH=1`, nvm `PROFILE=/dev/null`, Miniforge `-b`; PATH setup lives in `bash/custom.bash`. Downloads use `$ARCH`/`$GOARCH`, never a hardcoded `x86_64`. Installed tools are not upgraded.
- `symlinks.conf` lines are `source:target[:profile]` (`$(pwd)` = repo root; `symlinks.sh` cd's there). A source ending in `/*` links each matched file into the target directory. Lines with a profile apply only on that machine; `--delete` goes over every line. `--create` never overwrites a regular file unless `--backup` (moves it to `<target>.orig.<date>`). The config is eval'd, so editing the deployment means editing `symlinks.conf`, not the script.

## Linting / formatting

- **Python**: `ruff check <file>`, `ruff format <file>` — config in `ruff/ruff.toml`, which is linked to `~/.config/ruff` so ruff finds it anywhere (target py312, `E`/`F`/`I` with `E501` ignored, so the 120 line length is applied by the formatter only; isort with 2 blank lines after imports; double quotes). Type checking via `ty check <file>`.
- **Shell**: `shellcheck -x <file>` (sourced `utils.sh` is declared with `# shellcheck source-path=SCRIPTDIR source=...`); `shfmt -i 4` is Helix's bash formatter.
- Python dependencies are not managed by the repo: scripts run with whichever Python/conda env is active. `lib/.venv` is a local uv venv (Jupyter stack), not a dependency manifest; it and `.ruff_cache` stay out of git through their own internal `.gitignore`.

## Layout

- `install.sh` — new-machine entry point (see above).
- `bash/` — shell config, symlinked into `$HOME` and `$HOME/.config/bash/`. `.bashrc` sources `aliases.bash` + `custom.bash`; `custom.bash` builds PATH and tool env (rust/go/nvm/kerberos/helix/miniforge) and sources the untracked `~/.config/bash/local.bash` last (per-host settings and secrets go there, never in tracked files); `yabpc.bash` is the custom prompt (`PROMPT_COMMAND=yabpc`). Behavior branches on `$HPC_SYSTEM` (e.g. `juno`).
- `bin/` — user commands symlinked into `$HOME/.local/bin` on every machine; hyphenated names, no extension. They run through that link, so they find `scripts/utils.sh` via `readlink -f "${BASH_SOURCE[0]}"`.
  - LSF helpers (`tail-lsf-job`, `bkill-all`).
  - `.exp` Expect scripts (`kerb`, `vpn`, `juno`) automating interactive Kerberos/VPN/SSH login; they and `t2a.sh` read credentials from `pass` (`cmcc/juno/{user,password,authenticator}`) and make the OTP with `oathtool`.
  - `git-wt` runs as `git wt init <url> <dir> [<branch>[:<folder>]]...`: a worktree container (bare clone in `<dir>/.bare`, `<dir>/.git` pointing to it, fetch refspec for all remote branches, one worktree per branch with its upstream set, then `clean-branches`); `git wt clean-branches [-n] <dir>` removes the local branches a bare clone copies from the remote when they are not checked out and still equal `origin/<branch>` (via `update-ref -d <ref> <old>`), so `git worktree add <folder> <branch>` tracks `origin/<branch>`; `-n` prints/lists only.
  - `check-preproc REFERENCE_RUN COMPARISON_RUN [CYCLE_POINT...]` (Juno) compares the pre-processing outputs `<CYCLE_POINT>/<task>/out` of two runs (a longrun root, a pitest `CMCC_local/<name>/work`, a test archive of pre-processed inputs) before NEMO starts: same file names and no broken link, netCDF (`*.nc`, `*.NC`) by content with `xdiff dirs` (xdiffly; aliases `xdirs`/`xfiles` don't work in scripts), the other files with `cmp`; default tasks `ecmwf2nemo ecmwf2ww lobc sst prepobs` (`-t` to change), exit 1 on any difference.
  - `vault-snapshot` (laptop only) commits the user's own edits in the Obsidian vault `~/Obsidian/CMCC` as `User notes: auto-snapshot` and pushes it to `origin` (private GitLab); it skips a turn while git is busy or a file to commit (outside `.obsidian/`) changed in the last `QUIET_MIN` minutes, never commits `.obsidian/graph.json` (pathspec exclude) or the workspace files (the vault's `.gitignore`; an exclude naming an ignored path makes `git add` exit 1), `-n` is a dry run.
- `systemd/` — systemd user units symlinked into `$HOME/.config/systemd/user` (laptop profile only; enable them by hand with `systemctl --user enable --now <unit>`). `vault-snapshot.timer` runs `vault-snapshot.service` (→ `bin/vault-snapshot`) hourly, `Persistent=true`; the service never prompts for a passphrase (`GIT_TERMINAL_PROMPT=0`, `SSH_ASKPASS_REQUIRE=never`), so a push without the key in the agent fails and the next run retries.
- `lib/` — domain scripts run in place (NOT symlinked):
  - Ocean-model run management around Cylc/NEMO (`*_lobc*`, `*_hst_sla*`, `check_run.py`).
  - netCDF processing (`extract_nc_var.py`, `daily_mean.py`, `min_max4.py`, `assert_netcdf_same_except_dims.py`: two files equal apart from allowed dimension renames like `lon`→`longitude`).
  - CMEMS delivery: `generate_delivery_xml*.py` (product delivery manifests), `make_upl_sem.py` (UPL semaphore files, one per frequency), `check_my_timeseries.py` (MY timeseries check on MDS, imports `mds`), `prepare_dv_upload.py` (MDS DV test upload of MEDSEA ANFC 202611: one folder per dataset, two files each; dataset map embedded).
  - Longrun cleanup (dry-run unless `--apply`): `clean_longrun.py` (removes `nemo_ww/*out_*`, `nemo_ww/*1ts*`, `oceanvar/corr*` from the `<root>/YYYYMMDD` day folders in a date range), `clean_blk_restarts.py` (BLK/BSFS EAS9 longrun: removes the restarts of a date range from `restart/YYYYMMDDT2400` and from the `YYYYMMDD/analysis` Cylc work dir, keeping month-ends and the last N days; counts hard links to report the space really freed).
  - Accounting (`calc_core_hour.sh`, which reads `/users_home/.accounting/...` CSVs), and misc (`symmetric_encription.py`, a click CLI on `cryptography`).
- `scripts/` — repository setup only: `prerequisites.sh`, `symlinks.sh`, `utils.sh`. Daily tools go in `bin/` or `lib/`, not here.
- `claude/` — the user's **global** Claude Code config (`CLAUDE.md`, `settings.json`), linked into `~/.claude/`. Editing `claude/CLAUDE.md` changes instructions for every project, not just this repo.
- `helix/`, `wezterm/` (laptop profile only), `ruff/` — editor/tool config dirs, symlinked whole into `$HOME/.config/`.
- `templates/` — starter files for new scripts (`bash.sh`, `bash_getopt.sh`, `python_click.py`, `python_argparse.py`). Use these as the starting point when adding a new utility.

## Where new things go

- Command wanted on PATH on every machine → `bin/<hyphen-name>` (executable), then `scripts/symlinks.sh --create`.
- Domain / one-off script → `lib/`.
- Tool installable without root → an `ensure` line in `scripts/prerequisites.sh`; system package → `APT_PACKAGES` in `install.sh`.
- Config dir/file → its own folder + a `symlinks.conf` line (add `:laptop`/`:juno` if machine-specific).
- New scripts start with a header/docstring saying what they do and how to call them; Python scripts needing non-stdlib packages name them (or the conda env) there.
- Keep `README.md` (user-facing: new-machine steps, these rules) and this file in sync when the layout or setup changes.

## Conventions

- **`scripts/utils.sh` provides the logging primitives** (`info`/`success`/`warning`/`error`, colored via `tput`, plain when there is no terminal) and `detect_profile`. Bash scripts source it (`. "$SCRIPT_DIR/utils.sh"`) rather than re-implementing colored output. It also save/restores `xtrace`. Each log function prints only its first argument.
- Scripts resolve their own location with `SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"` and guard "run directly vs sourced" with `if [ "$(basename "$0")" = "$(basename "${BASH_SOURCE[0]}")" ]`. Follow this pattern so functions stay sourceable.
- HPC-specific paths and hostnames (`/work/cmcc/$USER`, `/users_home/.accounting`, `juno`, LSF `bjobs`/`bkill`, `$HOME/.lsbatch`) are hardcoded on purpose — they reflect the target cluster, not placeholders.
