# HpcEnv

Personal account settings and tooling for working on the CMCC HPC cluster
(`juno`, IBM **LSF** scheduler, **Kerberos** authentication).

The repository deploys shell, editor, and tool configuration into `$HOME` via
symlinks, bootstraps the toolchain, and keeps a set of helper scripts used in
day-to-day ocean-modeling workflows.

## Layout

| Path | Purpose |
|------|---------|
| `bash/` | Shell config: `.bashrc`, `aliases.bash`, `custom.bash` (PATH/env/functions), `yabpc.bash` (prompt), `miniforge3.bash` (conda init), git prompt/completion |
| `bin/` | User commands deployed to `~/.local/bin` (LSF helpers, Kerberos/VPN Expect scripts) |
| `helix/`, `wezterm/`, `ruff/` | Editor and tool configuration directories |
| `templates/` | Starter files for new bash/Python scripts |
| `scripts/` | Repository maintenance: deployment, prerequisites, shared helpers |
| `lib/` | Loose collection of HPC utilities, kept for reference (not deployed) |
| `symlinks.conf` | `source:target` map consumed by `scripts/symlinks.sh` |

## Installation

Install the toolchain (rust, go, uv, ruff, ty, helix, node, shellcheck,
language servers, lazygit). Steps are idempotent — already-installed tools are
skipped:

```bash
scripts/prerequisites.sh
```

Deploy the configuration symlinks defined in `symlinks.conf`:

```bash
scripts/symlinks.sh --create   # create or re-point links (idempotent)
scripts/symlinks.sh --delete   # remove the links
scripts/symlinks.sh --delete --include-files   # also remove real files at the targets
```

`--create` re-points stale links to the current source and never clobbers an
existing regular file. After editing `symlinks.conf`, re-run `--create` to apply
the change.

### Adding a tool to the bootstrap

`prerequisites.sh` is driven by a single `ensure` helper, so most tools are one
line in `main()`:

```bash
ensure <probe-binary> "<description>" <install command...>
```

`<probe-binary>` is the command used to detect that the tool is already present
(install is skipped when it is on `PATH`); the rest is the install command, run
verbatim. Examples for the common package managers:

```bash
ensure rg      "ripgrep"  cargo binstall -y ripgrep            # Rust  (cargo)
ensure ruff    "ruff"     uv tool install ruff@latest          # Python (uv)
ensure lazygit "lazygit"  go install github.com/jesseduffield/lazygit@latest  # Go
ensure bash-language-server "bash-language-server" npm i -g bash-language-server  # npm
```

Guidelines:

- Order matters — a tool's package manager must be installed and activated
  earlier in `main()` (the language blocks call `activate_rust`/`activate_go`/
  `activate_node` so `cargo`/`go`/`npm` work in the same run).
- Only installers that need a shell pipeline or multiple steps (e.g. a
  `curl … | sh` bootstrap, or downloading and unpacking a release tarball like
  Helix) get a dedicated `_install_*` function; pass that function name to
  `ensure` instead of an inline command.
- `ensure` detects "already installed" by probing a binary on `PATH`. If a tool
  can't be detected that way, check it inline outside `ensure` (no current tool
  needs this).

## Host-local settings

Machine-specific values — secrets, per-host variables, and anything that should
not be committed — go in an **untracked** `~/.config/bash/local.bash`. It is
sourced last by `custom.bash`, so it can override anything defined above it.

Some behavior also keys off the cluster-provided `HPC_SYSTEM` variable and the
`switch_user` function (e.g. the `myw`/`myd`/`@` aliases). These are guarded, so
the config is safe to deploy on a machine where they are absent.

Several scripts read credentials through [`pass`](https://www.passwordstore.org/)
(entries under `cmcc/juno/*`) together with `oathtool` for OTP — install and
populate those before using the Kerberos/VPN helpers.

## Conventions

- Shell scripts source `scripts/utils.sh` for colored logging
  (`info`/`success`/`warning`/`error`) instead of re-implementing it.
- Scripts resolve their own directory with `BASH_SOURCE` and guard
  "run directly vs. sourced" so their functions stay sourceable.
- Python is linted/formatted with `ruff` (config in `ruff/ruff.toml`, target
  py312) and type-checked with `ty`; shell scripts are checked with
  `shellcheck`.
- Start new scripts from the matching file in `templates/`.
