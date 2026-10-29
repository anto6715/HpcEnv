#!/usr/bin/env bash
#
# Install the user toolchain in $HOME (no root needed, so it also runs on Juno).
# Idempotent: anything already installed is skipped.
#
# Usage: prerequisites.sh [--check]
#   --check  only report what is missing, install nothing
#
# Adding a tool is a single line in main():
#     ensure <probe> "<description>" <install command...>
# e.g.
#     ensure rg "ripgrep" cargo binstall -y ripgrep
# <probe> is a binary looked up on PATH, or a path (containing a /) to an
# executable. Only installers that need a pipeline / multiple steps get a
# dedicated _install_* function; everything else is a plain command.
#
# The installers are told not to edit the shell rc files: ~/.bashrc is a link
# into this repo, and bash/custom.bash already sets up PATH for every tool.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source-path=SCRIPTDIR source=utils.sh
. "$SCRIPT_DIR/utils.sh"

# System tools every machine must already have (on the laptop install.sh
# installs them with apt; on Juno they come from the cluster).
BASE_TOOLS=(cc curl git tar gzip)

GO_VERSION="${GO_VERSION:-1.26.0}"
MINIFORGE_DIR="$HOME/.miniforge3" # same prefix as bash/miniforge3.bash

CHECK_ONLY=false
MISSING=() # --check: tools not installed
FAILED=()  # tools whose install failed or was skipped

# ---------------------------------------------------------------------------
# Core helpers
# ---------------------------------------------------------------------------

# have <binary> -> 0 if it is on PATH
have() { command -v "$1" &>/dev/null; }

# installed <probe> -> 0 if the binary is on PATH, or the path is executable
installed() {
    if [[ "$1" == */* ]]; then
        [ -x "$1" ]
    else
        have "$1"
    fi
}

# ensure <probe> <description> <install-cmd> [args...]
#   Runs the install command only when <probe> is not installed. The command
#   runs as real argv (no eval), so quoting is safe; installers that need a
#   pipeline pass a _install_* function instead. A command that is not
#   available (e.g. cargo after the Rust install failed) is reported as skipped.
ensure() {
    local probe="$1" desc="$2"
    shift 2
    if installed "$probe"; then
        info "${desc}: already installed"
        return 0
    fi
    if $CHECK_ONLY; then
        warning "${desc}: missing"
        MISSING+=("$desc")
        return 1
    fi
    if ! declare -F "$1" >/dev/null && ! have "$1"; then
        error "${desc}: skipped, '$1' is not available"
        FAILED+=("$desc")
        return 1
    fi
    info "Installing ${desc}..."
    if ! "$@"; then
        error "${desc}: install FAILED"
        FAILED+=("$desc")
        return 1
    fi
    activate
    if ! installed "$probe"; then
        error "${desc}: installed, but '${probe}' is not found afterwards"
        FAILED+=("$desc")
        return 1
    fi
    success "${desc}: installed"
}

# check_base_tools -> 0 if every BASE_TOOLS binary is on PATH
check_base_tools() {
    local missing=() tool
    for tool in "${BASE_TOOLS[@]}"; do
        have "$tool" || missing+=("$tool")
    done
    if ((${#missing[@]})); then
        error "Missing system tools: ${missing[*]}"
        error "On Debian/Ubuntu run ./install.sh, or: sudo apt install build-essential curl git tar gzip"
        return 1
    fi
    info "System tools: ${BASE_TOOLS[*]} found"
}

# Architecture names used by the downloads below
case "$(uname -m)" in
    x86_64) ARCH="x86_64" GOARCH="amd64" ;;
    aarch64 | arm64) ARCH="aarch64" GOARCH="arm64" ;;
    *) ARCH="$(uname -m)" GOARCH="$ARCH" ;;
esac

# ---------------------------------------------------------------------------
# Activation: put every toolchain on PATH in *this* shell. The script does not
# read ~/.bashrc, so without this a tool installed a few lines above (uv,
# cargo, go...) is not found, and on re-runs installed tools look missing.
# Safe to call many times.
# ---------------------------------------------------------------------------

activate() {
    PATH="$HOME/.local/bin:$PATH"
    # shellcheck source=/dev/null
    [ -f "$HOME/.cargo/env" ] && . "$HOME/.cargo/env"
    [ -x "$HOME/opt/go/bin/go" ] && PATH="$HOME/opt/go/bin:$PATH"
    have go && PATH="$(go env GOPATH)/bin:$PATH"
    export NVM_DIR="$HOME/.nvm"
    # shellcheck source=/dev/null
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
    # Appended, so conda's python does not shadow the system one
    [ -d "$MINIFORGE_DIR/bin" ] && PATH="$PATH:$MINIFORGE_DIR/bin"
    export PATH
    hash -r
}

# ---------------------------------------------------------------------------
# Bespoke installers (pipelines / multi-step) — just the action, no guard
# ---------------------------------------------------------------------------

_install_rust() {
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --no-modify-path
}

_install_cargo_binstall() {
    # Prebuilt binary into ~/.cargo/bin: no compile, no C toolchain needed
    curl -L --proto '=https' --tlsv1.2 -sSf \
        https://raw.githubusercontent.com/cargo-bins/cargo-binstall/main/install-from-binstall-release.sh | bash
}

_install_go() {
    # Go must be unpacked into an empty dir: a new version over an old one breaks
    rm -rf "$HOME/opt/go"
    curl -fLsS "https://go.dev/dl/go${GO_VERSION}.linux-${GOARCH}.tar.gz" | tar -C "$HOME/opt" -xzf -
}

_install_uv() {
    curl -LsSf https://astral.sh/uv/install.sh | env UV_NO_MODIFY_PATH=1 sh
}

# shellcheck source=/dev/null
_install_node() {
    # Install nvm (PROFILE=/dev/null: don't edit the rc files), load it into
    # this shell, then install Node.
    curl -fsSL -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.4/install.sh | PROFILE=/dev/null bash &&
        export NVM_DIR="$HOME/.nvm" &&
        \. "$NVM_DIR/nvm.sh" &&
        nvm install 24
}

_install_miniforge() {
    # Batch mode (-b) doesn't run `conda init`: bash/miniforge3.bash does that
    local tmp rc
    tmp="$(mktemp -d)" || return 1
    curl -fsSL -o "$tmp/miniforge.sh" \
        "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-${ARCH}.sh" &&
        bash "$tmp/miniforge.sh" -b -p "$MINIFORGE_DIR"
    rc=$?
    rm -rf "$tmp"
    return $rc
}

_install_shellcheck() {
    local tmp rc
    have xz || { error "shellcheck install needs 'xz' (apt install xz-utils)"; return 1; }
    tmp="$(mktemp -d)" || return 1
    curl -fsSL "https://github.com/koalaman/shellcheck/releases/download/stable/shellcheck-stable.linux.${ARCH}.tar.xz" |
        tar -xJ -C "$tmp" &&
        mv "$tmp/shellcheck-stable/shellcheck" "$HOME/.local/bin/"
    rc=$?
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
    case "$ARCH" in
        x86_64) subdir="linux-64" ;;
        aarch64) subdir="linux-aarch64" ;;
        *) error "Unsupported architecture for Helix: $ARCH"; return 1 ;;
    esac

    have unzip || { error "Helix install needs 'unzip' (apt install unzip)"; return 1; }
    have zstd || { error "Helix install needs 'zstd' (apt install zstd, or the one in Miniforge)"; return 1; }

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
# Orchestration
# ---------------------------------------------------------------------------

usage() {
    echo "Usage: $(basename "$0") [--check]"
}

# summary -> prints what is missing / failed; 1 if anything is
summary() {
    if $CHECK_ONLY && ((${#MISSING[@]})); then
        warning "Missing (${#MISSING[@]}): ${MISSING[*]}"
        return 1
    fi
    if ((${#FAILED[@]})); then
        error "Failed or skipped (${#FAILED[@]}): ${FAILED[*]}"
        return 1
    fi
    success "Toolchain complete"
}

main() {
    case "${1:-}" in
        "") ;;
        --check) CHECK_ONLY=true ;;
        -h | --help) usage; return 0 ;;
        *) error "Unknown argument '$1'"; usage; return 1 ;;
    esac

    mkdir -p "$HOME/.local/bin" "$HOME/opt"
    activate

    if ! check_base_tools && ! $CHECK_ONLY; then
        return 1
    fi

    # === Languages / package managers (must come first) === #
    ensure rustc "Rust" _install_rust
    ensure go "Go ${GO_VERSION}" _install_go
    ensure uv "uv" _install_uv
    ensure node "Node.js" _install_node
    ensure "$MINIFORGE_DIR/bin/conda" "Miniforge (conda/mamba)" _install_miniforge

    # === Rust tools === #
    ensure cargo-binstall "cargo-binstall" _install_cargo_binstall
    ensure rg "ripgrep" cargo binstall -y ripgrep
    ensure zellij "zellij" cargo binstall -y zellij
    # musl target -> static binary with no glibc dependency (HPC glibc is old)
    ensure yazi "yazi-fm" cargo binstall --targets "${ARCH}-unknown-linux-musl" -y yazi-fm

    # === Python (uv) tools === #
    ensure ruff "ruff" uv tool install ruff@latest
    ensure ty "ty" uv tool install ty@latest
    ensure xdiff "xdiffly" uv tool install --python 3.13 xdiffly
    # rofs-exp's run-manifest (bin/run-ref drives it): installed from the repo
    # over ssh, pinned to one branch. After a change of the package there:
    #   uv tool upgrade run-manifest
    ensure run-manifest "run-manifest" uv tool install --python 3.13 \
        "run-manifest @ git+ssh://git@github.com/CMCC-Foundation/rofs-exp@cmcc/bsfs_assw/fix#subdirectory=CMCC_local/tools/run_manifest"

    # === Go tools === #
    ensure yamlfmt "yamlfmt" go install github.com/google/yamlfmt/cmd/yamlfmt@latest
    ensure shfmt "shfmt" go install mvdan.cc/sh/v3/cmd/shfmt@latest
    ensure golangci-lint "golangci-lint" _install_golangci_lint
    ensure golangci-lint-langserver "golangci-lint-langserver" go install github.com/nametake/golangci-lint-langserver@latest
    ensure lazygit "lazygit" go install github.com/jesseduffield/lazygit@latest

    # === Node / npm tools === #
    ensure bash-language-server "bash-language-server" npm i -g bash-language-server
    ensure yaml-language-server "yaml-language-server" npm i -g yaml-language-server

    # === Editors / misc === #
    ensure hx "Helix" _install_helix
    ensure shellcheck "shellcheck" _install_shellcheck

    summary
}

if [ "$(basename "$0")" = "$(basename "${BASH_SOURCE[0]}")" ]; then
    main "$@"
fi
