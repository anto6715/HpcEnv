#!/usr/bin/env bash
#
# Bootstrap the local toolchain. Idempotent: anything already on PATH is skipped.
#
# Adding a tool is a single line in main():
#     ensure <probe-binary> "<description>" <install command...>
# e.g.
#     ensure rg "ripgrep" cargo binstall -y ripgrep
#
# Only installers that need a shell pipeline / multiple steps get a dedicated
# _install_* function; everything else is a plain command passed to ensure.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

. "$SCRIPT_DIR/utils.sh"

# ---------------------------------------------------------------------------
# Core helpers
# ---------------------------------------------------------------------------

# have <binary> -> 0 if it is already on PATH
have() { command -v "$1" &>/dev/null; }

# ensure <probe-binary> <description> <install-cmd> [args...]
#   Runs the install command only when <probe-binary> is not already on PATH.
#   The command is run as real argv (no eval), so quoting is safe; installers
#   that need a pipeline pass a _install_* function as the command instead.
ensure() {
    local probe="$1" desc="$2"
    shift 2
    info "Installing ${desc}..."
    if have "$probe"; then
        warning "${desc} already installed — skipping"
        return 0
    fi
    if "$@"; then
        success "${desc} installed"
    else
        error "${desc} install FAILED"
        return 1
    fi
}

# ---------------------------------------------------------------------------
# Bespoke installers (pipelines / multi-step) — just the action, no guard
# ---------------------------------------------------------------------------

_install_rust() {
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
}

_install_go() {
    curl -LsSf https://go.dev/dl/go1.26.0.linux-amd64.tar.gz | tar -C "$HOME/opt" -xzf -
}

_install_uv() {
    curl -LsSf https://astral.sh/uv/install.sh | sh
}

_install_node() {
    # Download and install nvm, then load it into this shell and install Node.
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.4/install.sh | bash &&
        \. "$HOME/.nvm/nvm.sh" &&
        nvm install 24
}

_install_shellcheck() {
    local tmp
    tmp="$(mktemp -d)" || return 1
    wget -qO- https://github.com/koalaman/shellcheck/releases/download/stable/shellcheck-stable.linux.x86_64.tar.xz |
        tar -xJ -C "$tmp" &&
        mv "$tmp/shellcheck-stable/shellcheck" "$HOME/.local/bin/"
    local rc=$?
    rm -rf "$tmp"
    return $rc
}

_install_golangci_lint() {
    # binary lands in $(go env GOPATH)/bin/golangci-lint
    curl -sSfL https://golangci-lint.run/install.sh | sh -s -- -b "$(go env GOPATH)/bin" v2.10.1
}

_install_helix() {
    # Install Helix from the conda-forge *binary* (without using conda). The
    # upstream GitHub binary needs glibc >= 2.29, which is too new for the HPC
    # nodes; the conda-forge build targets an old sysroot (glibc <= 2.16), links
    # only system libraries, and finds its bundled runtime relative to itself.
    # So we just unpack it into $HOME/opt/helix — no conda env, no HELIX_RUNTIME
    # needed (and $HOME/opt/helix/runtime still matches what custom.bash exports).
    local subdir
    case "$(uname -m)" in
        x86_64) subdir="linux-64" ;;
        aarch64 | arm64) subdir="linux-aarch64" ;;
        *) error "Unsupported architecture for Helix: $(uname -m)"; return 1 ;;
    esac

    have unzip || { error "Helix install needs 'unzip'"; return 1; }
    have zstd || { error "Helix install needs 'zstd' (ships with mamba)"; return 1; }

    # Resolve the conda-forge package URL with curl+grep (no jq).
    # Override the version by exporting HELIX_VERSION.
    local ver file url tmp
    ver="${HELIX_VERSION:-$(curl -fsSL https://api.anaconda.org/package/conda-forge/helix |
        grep -oE '"latest_version": *"[^"]*"' | grep -oE '[0-9][^"]*')}"
    [ -n "$ver" ] || { error "Could not resolve latest Helix version"; return 1; }
    file="$(curl -fsSL https://api.anaconda.org/package/conda-forge/helix/files |
        grep -oE "${subdir}/helix-${ver}-[^\"]*\.conda" | sort -V | tail -1)"
    [ -n "$file" ] || { error "No conda-forge Helix build for ${ver}/${subdir}"; return 1; }
    url="https://conda.anaconda.org/conda-forge/${file}"

    tmp="$(mktemp -d)" || return 1
    # A .conda is a zip of zstd tarballs; the binary + runtime live under
    # libexec/helix/ in the pkg-*.tar.zst member.
    if curl -fsSL "$url" -o "$tmp/helix.conda" &&
        unzip -q "$tmp/helix.conda" -d "$tmp" &&
        tar --use-compress-program=zstd -xf "$tmp"/pkg-*.tar.zst -C "$tmp"; then
        rm -rf "$HOME/opt/helix"
        mkdir -p "$HOME/opt/helix"
        mv "$tmp/libexec/helix/hx" "$tmp/libexec/helix/runtime" "$HOME/opt/helix/"
        ln -sfn "$HOME/opt/helix/hx" "$HOME/.local/bin/hx"
        rm -rf "$tmp"
    else
        error "Helix install failed: $url"
        rm -rf "$tmp"
        return 1
    fi
}

# ---------------------------------------------------------------------------
# Activation: a freshly-installed toolchain's package manager is not yet on
# PATH in *this* shell (the installer only edited the shell rc files). Source
# it so the tool installs below can actually run in the same run.
# ---------------------------------------------------------------------------

activate_rust() { [ -f "$HOME/.cargo/env" ] && . "$HOME/.cargo/env"; }
activate_go() {
    # Put go on PATH first, then query GOPATH (an unset GOPATH/bin would
    # otherwise be lost on a fresh install where `go` isn't yet reachable).
    export PATH="$HOME/opt/go/bin:$PATH"
    local gopath
    gopath="$(go env GOPATH 2>/dev/null)"
    [ -n "$gopath" ] && export PATH="$gopath/bin:$PATH"
}
activate_node() {
    export NVM_DIR="$HOME/.nvm"
    # shellcheck source=/dev/null
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
}

# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

main() {
    mkdir -p "$HOME/.local/bin" "$HOME/opt"

    # === Languages / package managers (must come first, then activate) === #
    ensure rustc "Rust" _install_rust && activate_rust
    ensure go "Go" _install_go && activate_go
    ensure uv "uv" _install_uv
    ensure node "Node.js" _install_node && activate_node

    # === Rust tools === #
    ensure cargo-binstall "cargo-binstall" cargo install cargo-binstall
    ensure rg "ripgrep" cargo binstall -y ripgrep
    # musl target -> static binary with no glibc dependency (HPC glibc is old)
    ensure yazi "yazi-fm" cargo binstall --targets x86_64-unknown-linux-musl -y yazi-fm

    # === Python (uv) tools === #
    ensure ruff "ruff" uv tool install ruff@latest
    ensure ty "ty" uv tool install ty@latest
    ensure xdiff "xdiffly" uv tool install --python 3.13 xdiffly

    # === Go tools === #
    ensure yamlfmt "yamlfmt" go install github.com/google/yamlfmt/cmd/yamlfmt@latest
    ensure golangci-lint "golangci-lint" _install_golangci_lint
    ensure golangci-lint-langserver "golangci-lint-langserver" go install github.com/nametake/golangci-lint-langserver@latest
    ensure lazygit "lazygit" go install github.com/jesseduffield/lazygit@latest

    # === Node / npm tools === #
    ensure bash-language-server "bash-language-server" npm i -g bash-language-server
    ensure yaml-language-server "yaml-language-server" npm i -g yaml-language-server

    # === Editors / misc === #
    ensure hx "Helix" _install_helix
    ensure shellcheck "shellcheck" _install_shellcheck
}

if [ "$(basename "$0")" = "$(basename "${BASH_SOURCE[0]}")" ]; then
    main "$@"
fi
