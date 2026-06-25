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
    ensure yazi "yazi-fm" cargo binstall -y yazi-fm

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

    # === Editors / misc (special-cased: probe is a directory, not a binary) === #
    info "Cloning Helix..."
    if [ -d "$HOME/opt/helix" ]; then
        warning "Helix already cloned — skipping"
    else
        git clone https://github.com/helix-editor/helix.git "$HOME/opt/helix" &&
            success "Helix cloned"
    fi

    ensure shellcheck "shellcheck" _install_shellcheck
}

if [ "$(basename "$0")" = "$(basename "${BASH_SOURCE[0]}")" ]; then
    main "$@"
fi
