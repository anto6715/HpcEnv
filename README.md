# HpcEnv

Personal account settings and tooling, so moving to a new machine (a new
laptop, or the CMCC HPC cluster `juno`, IBM **LSF** scheduler, **Kerberos**
authentication) brings along the same shell, editor, tools and helper scripts.

The repository installs the toolchain into `$HOME`, links the shell/editor/tool
configuration into place, and keeps the helper scripts used in day-to-day
ocean-modeling workflows.

## New machine

```bash
# HTTPS works before the SSH keys are set up; switch to the SSH remote later with
#   git remote set-url origin git@github.com:anto6715/HpcEnv.git
git clone https://github.com/anto6715/HpcEnv.git ~/git/HpcEnv
cd ~/git/HpcEnv

./install.sh --check    # what is missing; changes nothing
./install.sh --backup   # install everything, then link the config
```

`--backup` lets the links replace the files a fresh system ships (e.g. its
`~/.bashrc`), keeping them as `<file>.orig.<date>`; see
[A file is in the way](#a-file-is-in-the-way).

`install.sh` runs, in order:

1. **System packages** with `apt` (laptop only, asks for the sudo password):
   compiler, `curl`, `unzip`/`zstd`, `pass`, `oathtool`, `expect`, `krb5-user`,
   `xclip`... The list is `APT_PACKAGES` in `install.sh`.
2. **User toolchain** in `$HOME` with `scripts/prerequisites.sh` (no root, so it
   also runs on Juno).
3. **Config symlinks** from `symlinks.conf` with `scripts/symlinks.sh`.
4. **The steps left to do by hand**, printed at the end: GPG key and `pass`
   store, SSH keys, Kerberos realm, apps that aren't in apt, systemd timer.

It is safe to re-run: anything already in place is skipped. It exits 1 when a
step failed, with the list of what failed.

`cargo binstall` asks the GitHub API where each release is. Without a token
GitHub allows few requests per hour, and it then waits and retries (403
messages, slow install). Export a token (no scopes needed) first to avoid it:
`export GITHUB_TOKEN=<token>`.

### Profiles

The machine profile decides which system packages and links apply:

| Profile | Detected when | Differences |
|---------|---------------|-------------|
| `juno` | `HPC_SYSTEM=juno`, or the hostname contains `juno` | no apt (no sudo); no WezTerm or systemd links |
| `laptop` | anywhere else | apt packages; all links |

Override the detection with `./install.sh --profile laptop|juno`.

### A file is in the way

Without `--backup` a regular file is never overwritten. A fresh system usually
ships its own `~/.bashrc`, which is then reported as "left alone" and the run
exits 1. Move such files aside (`<target>.orig.<date>`) and link with either:

```bash
./install.sh --backup
scripts/symlinks.sh --create --backup   # links only
```

## Layout

| Path | Purpose |
|------|---------|
| `install.sh` | Entry point for a new machine (see above) |
| `bash/` | Shell config: `.bashrc`, `aliases.bash`, `custom.bash` (PATH/env/functions), `yabpc.bash` (prompt), `miniforge3.bash` (conda init), git prompt/completion |
| `bin/` | Commands linked into `~/.local/bin` on every machine (LSF helpers, Kerberos/VPN Expect scripts, `git-wt`, `vault-snapshot`, `check-preproc`) |
| `lib/` | Domain scripts run in place, not installed (Cylc/NEMO run management, netCDF processing, CMEMS delivery, longrun cleanup, accounting) |
| `scripts/` | Repository setup only: `prerequisites.sh`, `symlinks.sh`, `utils.sh` |
| `claude/` | Global Claude Code config, linked into `~/.claude/` |
| `systemd/` | systemd user units linked into `~/.config/systemd/user` (laptop: hourly `vault-snapshot` timer) |
| `helix/`, `wezterm/`, `ruff/` | Editor and tool configuration directories |
| `templates/` | Starter files for new bash/Python scripts |
| `symlinks.conf` | `source:target[:profile]` map consumed by `scripts/symlinks.sh` |

## Where new things go

| You are adding | Put it in | Then |
|----------------|-----------|------|
| A command to have on `PATH` on every machine | `bin/<name>` | see [Adding a script](#adding-a-script) |
| A domain script run from its folder (one-off, project-specific) | `lib/` | run it as `lib/<script>` |
| A tool installed without root (cargo, uv, go, npm, a download) | an `ensure` line in `scripts/prerequisites.sh` | see [Adding a tool](#adding-a-tool-to-the-bootstrap) |
| A system package (needs sudo) | `APT_PACKAGES` in `install.sh` | re-run `./install.sh` |
| A config file or folder | its own folder at the repo root + a line in `symlinks.conf` | `scripts/symlinks.sh --create` |
| A per-host setting or a secret | `~/.config/bash/local.bash` (untracked) | — |

`scripts/` is only for setting up the repo itself; tools for daily work go in
`bin/` or `lib/`.

### Adding a script

1. Start from the matching file in `templates/` (`bash.sh`, `bash_getopt.sh`,
   `python_argparse.py`, `python_click.py`).
2. Start with a header comment (bash) or docstring (Python) that says what the
   script does and how to call it. For a Python script that needs packages
   outside the standard library, say there which packages or conda environment
   it needs: this repo does not install Python dependencies.
3. In `bin/`: name it with hyphens and no extension (`check-preproc`, not
   `check_preproc.sh`), make it executable (`chmod +x`), and run
   `scripts/symlinks.sh --create` to link it. It runs through a link in
   `~/.local/bin`, so to source `scripts/utils.sh` resolve the real path first,
   as `bin/git-wt` does:

   ```bash
   script_dir=$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)
   . "${script_dir}/../scripts/utils.sh"
   ```

4. Lint it: `shellcheck -x <script>` for bash, `ruff check <script>` and
   `ruff format <script>` for Python.

### Adding a tool to the bootstrap

`prerequisites.sh` is driven by a single `ensure` helper, so most tools are one
line in `main()`:

```bash
ensure <probe> "<description>" <install command...>
```

`<probe>` detects that the tool is already present (the install is then
skipped): a binary looked up on `PATH`, or a path (containing a `/`) to an
executable, like `$MINIFORGE_DIR/bin/conda`. The rest is the install command,
run verbatim. Examples for the common package managers:

```bash
ensure rg      "ripgrep"  cargo binstall -y ripgrep            # Rust  (cargo)
ensure ruff    "ruff"     uv tool install ruff@latest          # Python (uv)
ensure lazygit "lazygit"  go install github.com/jesseduffield/lazygit@latest  # Go
ensure bash-language-server "bash-language-server" npm i -g bash-language-server  # npm
```

Guidelines:

- A tool's package manager must be installed earlier in `main()`. Every
  toolchain (`~/.local/bin`, cargo, go, nvm, Miniforge) is put on `PATH` at the
  start and again after each install, so a tool installed a few lines above can
  be used right away. If the package manager is missing (its install failed),
  the tool is reported as skipped instead of failing with "command not found".
- Only installers that need a shell pipeline or multiple steps (e.g. a
  `curl … | sh` bootstrap, or downloading and unpacking a release tarball like
  Helix) get a dedicated `_install_*` function; pass that function name to
  `ensure` instead of an inline command.
- Installers must not edit the shell rc files (`~/.bashrc` is a link into this
  repo): pass their "don't modify PATH" option, as rustup (`--no-modify-path`),
  uv (`UV_NO_MODIFY_PATH=1`) and nvm (`PROFILE=/dev/null`) do. Put the PATH
  setup in `bash/custom.bash` instead.
- Downloads pick the architecture from `$ARCH` (`x86_64`/`aarch64`) or
  `$GOARCH` (`amd64`/`arm64`); don't hardcode `x86_64`.
- Already-installed tools are not upgraded. Go is pinned by `GO_VERSION`: to
  upgrade, `rm -rf ~/opt/go` and run `GO_VERSION=<x.y.z> scripts/prerequisites.sh`.

## Host-local settings

Machine-specific values — secrets, per-host variables, and anything that should
not be committed — go in an **untracked** `~/.config/bash/local.bash`. It is
sourced last by `custom.bash`, so it can override anything defined above it.

Some behavior also keys off the cluster-provided `HPC_SYSTEM` variable and the
`switch_user` function (e.g. the `myw`/`myd`/`@` aliases). These are guarded, so
the config is safe to deploy on a machine where they are absent.

Several scripts read credentials through [`pass`](https://www.passwordstore.org/)
(entries under `cmcc/juno/*`) together with `oathtool` for OTP — restore the
GPG key and the password store before using the Kerberos/VPN helpers.

## Conventions

- Shell scripts source `scripts/utils.sh` for colored logging
  (`info`/`success`/`warning`/`error`) instead of re-implementing it.
- Scripts resolve their own directory with `BASH_SOURCE` and guard
  "run directly vs. sourced" so their functions stay sourceable.
- Python is linted/formatted with `ruff` (config in `ruff/ruff.toml`, target
  py312) and type-checked with `ty`; shell scripts are checked with
  `shellcheck`.
