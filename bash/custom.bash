#!/usr/bin/env bash

__bash_aliases_path__=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# PATH
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

PATH="$HOME/.local/bin:$PATH"

## Kerberos
[ -d "/usr/local/opt/krb5/bin" ] && PATH="/usr/local/opt/krb5/bin:$PATH"

# OpenCode
[ -d "$HOME/.opencode/bin" ] && PATH="$PATH:$HOME/.opencode/bin"

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Custom prompt
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
if [ -f "$HOME/.config/bash/yabpc.bash" ]; then
    . "$HOME/.config/bash/yabpc.bash"
    PROMPT_COMMAND=yabpc
fi

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# LIBRARIES
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

## GoLang
if [ -d "$HOME/opt/go/" ]; then
    PATH="$PATH:$HOME/opt/go/bin"
    # equivalent of go env GOEN
    PATH="$PATH:$HOME/go/bin"
fi

## Rust
[ -d "$HOME/.cargo" ] && . "$HOME/.cargo/env"

## NVM
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"                   # This loads nvm
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion" # This loads nvm bash_completion

## Tilix
if [ $TILIX_ID ] || [ $VTE_VERSION ]; then
    source /etc/profile.d/vte.sh
fi

## Kerberos
export KRB5CCNAME=FILE:/tmp/krb5cc_$(id -u)

## Helix
export HELIX_RUNTIME="$HOME/opt/helix/runtime"

## Yazi
export EDITOR=hx

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Bash History
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# Avoid duplicates and leading-space commands
export HISTCONTROL=ignoreboth

# Large, useful history
export HISTSIZE=10000
export HISTFILESIZE=200000
export HISTFILE="$HOME/.bash_history"

# Append instead of overwrite
shopt -s histappend

# Save multi-line commands as one entry
shopt -s cmdhist

# Timestamp history entries
export HISTTIMEFORMAT='%F %T  '

# Sync history safely between sessions
__history_sync() {
    history -a # write new lines
    history -n # read new lines
}

# Add to PROMPT_COMMAND safely (no duplication)
case "$PROMPT_COMMAND" in
*__history_sync*) ;;
*) PROMPT_COMMAND="__history_sync${PROMPT_COMMAND:+; $PROMPT_COMMAND}" ;;
esac

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Bash Terminal
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# update the values of LINES and COLUMNS.
shopt -s checkwinsize

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Conda
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

[ -f "$HOME/.config/bash/miniforge3.bash" ] && . "$HOME/.config/bash/miniforge3.bash"

# force the export of this function to remove any issue with `conda activate` command
# Use `command -v` (not `which`): conda is a shell function, which an external
# `which` cannot see, so `export -f` below would otherwise be skipped.
if command -v conda &>/dev/null; then
    export -f conda
    export -f __conda_exe
    export -f __conda_activate
    export -f __conda_reactivate
    export -f __conda_hashr
fi

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# AUTOCOMPLETE
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

## BASH
if ! shopt -oq posix; then
    if [ -f /usr/share/bash-completion/bash_completion ]; then
        . /usr/share/bash-completion/bash_completion
    elif [ -f /etc/bash_completion ]; then
        . /etc/bash_completion
    fi
fi

## Git
[ -f "$HOME/.config/bash/git-prompt.sh" ] && . "$HOME/.config/bash/git-prompt.sh"
[ -f "$HOME/.config/bash/git-completion.bash" ] && . "$HOME/.config/bash/git-completion.bash"

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# FUNCTIONS
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

bjobs-stats() {
    local user="${1:-"$(whoami)"}"
    bjobs -a -o "jobid stat job_name run_time start_time finish_time exec_host" -u "${user}" | sort
}
export -f bjobs-stats

#
# # ex - archive extractor
# # usage: ex <file>
ex() {
    if [ -f $1 ]; then
        case $1 in
        *.tar.bz2) tar xjf $1 ;;
        *.tar.gz) tar xzf $1 ;;
        *.tar.xz) tar xvf $1 ;;
        *.bz2) bunzip2 $1 ;;
        *.rar) unrar x $1 ;;
        *.gz) gunzip $1 ;;
        *.tar) tar xf $1 ;;
        *.tbz2) tar xjf $1 ;;
        *.tgz) tar xzf $1 ;;
        *.zip) unzip $1 ;;
        *.Z) uncompress $1 ;;
        *.7z) 7z x $1 ;;
        *) echo "'$1' cannot be extracted via ex()" ;;
        esac
    else
        echo "'$1' is not a valid file"
    fi
}

# Recommended to start yazi
function y() {
	local tmp="$(mktemp -t "yazi-cwd.XXXXXX")" cwd
	command yazi "$@" --cwd-file="$tmp"
	IFS= read -r -d '' cwd < "$tmp"
	[ "$cwd" != "$PWD" ] && [ -d "$cwd" ] && builtin cd -- "$cwd"
	rm -f -- "$tmp"
}

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Host-local overrides
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# Machine-specific settings (secrets, per-host variables, etc.) belong in an
# untracked local.bash so they stay out of version control. Sourced last so it
# can override anything defined above.
[ -f "$HOME/.config/bash/local.bash" ] && . "$HOME/.config/bash/local.bash"
