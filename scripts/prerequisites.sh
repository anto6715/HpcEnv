#!/usr/bin/env bash
#
# Get the absolute path of the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

. $SCRIPT_DIR/utils.sh

install_rust() {
    info "Installing Rust..."
    if hash rustc &>/dev/null; then
        warning "Rust already installed"
    else
        curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
    fi
}

install_uv() {
    info "Installing uv..."
    if hash uv &>/dev/null; then
        warning "uv already installed"
    else
        curl -LsSf https://astral.sh/uv/install.sh | sh
    fi
}

install_ruff() {
    info "Installing ruff..."
    if hash ruff &>/dev/null; then
        warning "ruff already installed"
    else
        # use uv to install ruff globally
        uv tool install ruff@latest
    fi
}

install_ty() {
    info "Installing typer..."
    if hash ty &>/dev/null; then
        warning "typer already installed"
    else
        # use uv to install typer globally
        uv tool install ty@latest
    fi
}

clone_helix() {
    info "Cloning Helix..."
    if [ -d "$HOME/opt/helix" ]; then
        warning "Helix already cloned"
    else
        git clone https://github.com/helix-editor/helix.git "$HOME/opt/helix"
    fi
}

if [ "$(basename "$0")" = "$(basename "${BASH_SOURCE[0]}")" ]; then
    install_rust
    install_uv
    install_ruff
    install_ty

    clone_helix
fi
