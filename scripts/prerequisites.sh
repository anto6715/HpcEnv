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

download_golang() {
    info "Downloading Go..."
    if hash go &>/dev/null; then
        warning "Go already installed"
    else
        curl -LsSf https://go.dev/dl/go1.26.0.linux-amd64.tar.gz | tar -C $HOME/opt -xzf -
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

install_yamlfmt() {
    info "Installing yamlft..."
    if hash yamlfmt &>/dev/null; then
        warning "yamlfmt already installed"
    else
        go install github.com/google/yamlfmt/cmd/yamlfmt@latest
    fi
}

install_yaml_language_server() {
    info "Installing yaml language server..."
    if hash yaml-language-server &>/dev/null; then
        warning "yaml-language-server already installed"
    else
        npm i -g yaml-language-server
    fi
}

install_golangci_lint() {
    info "Installing golangci-lint..."
    if hash golangci-lint &>/dev/null; then
        warning "golangci-lint already installed"
    else
        # binary will be $(go env GOPATH)/bin/golangci-lint
        curl -sSfL https://golangci-lint.run/install.sh | sh -s -- -b $(go env GOPATH)/bin v2.10.1

    fi
    info "Installing ggolangci-lint-langserver..."
    if hash golangci-lint-langserver &>/dev/null; then
        warning "golangci-lint-langserver already installed"
    else
        go install github.com/nametake/golangci-lint-langserver@latest
    fi
}

install_lazygit() {
    info "Installing lazygit..."
    if hash lazygit &>/dev/null; then
        warning "lazygit already installed"
    else
        go install github.com/jesseduffield/lazygit@latest
    fi
}

if [ "$(basename "$0")" = "$(basename "${BASH_SOURCE[0]}")" ]; then
    # === Languages === #
    install_rust
    download_golang

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

    # Yaml
    install_yamlfmt
    install_yaml_language_server

    # GoLang tools
    install_golangci_lint
    install_lazygit

fi
