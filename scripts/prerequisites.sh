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

install_shellcheck() {
    info "Installing shellcheck..."
    if hash shellcheck &>/dev/null; then
        warning "shellcheck already installed"
    else
        mkdir /tmp/shellcheck
        wget https://github.com/koalaman/shellcheck/releases/download/stable/shellcheck-stable.linux.x86_64.tar.xz -P /tmp/shellcheck
        tar xvf /tmp/shellcheck/shellcheck-stable.linux.x86_64.tar.xz -C /tmp/shellcheck
        mv /tmp/shellcheck/shellcheck-stable/shellcheck "$HOME/.local/bin"
    fi
}

install_nodejs() {
    info "Installing nodejs..."
    if hash nodejs &>/dev/null; then
        warning "nodejs already installed"
    else
        # Download and install nvm:
        curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.4/install.sh | bash
        # in lieu of restarting the shell
        \. "$HOME/.nvm/nvm.sh"
        # Download and install Node.js:
        nvm install 24
        # Verify the Node.js version:
        node -v # Should print "v24.14.0".
        # Verify npm version:
        npm -v # Should print "11.9.0".
    fi
}

install_bash_language_server() {
    info "Installing bash-language-server..."
    if hash bash-language-server &>/dev/null; then
        warning "bash-language-server already installed"
    else
        npm i -g bash-language-server
    fi
}

if [ "$(basename "$0")" = "$(basename "${BASH_SOURCE[0]}")" ]; then
    # === Rust === #
    install_rust

    # === Python === #
    install_uv
    install_ruff
    install_ty

    # Tools
    clone_helix
    install_nodejs

    # BASH
    install_shellcheck
    install_bash_language_server
fi
