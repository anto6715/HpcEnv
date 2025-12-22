__bash_aliases_path__=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Bash completion for git
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

if [ -r /usr/share/doc/git/contrib/completion/git-prompt.sh ]; then
  . "$__bash_aliases_path__"/git/git-prompt.sh
fi

if [ -r /usr/share/doc/git/contrib/completion/git-completion.bash ]; then
  . "$__bash_aliases_path__"/git/git-completion.bash
fi

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Custom prompt
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

source "$__bash_aliases_path__/yabpc.bash"
PROMPT_COMMAND=yabpc

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Aliases
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# Move between partitions
alias myw='cd /work/cmcc/$USER'
alias myd='cd /data/cmcc/$USER'

# bash cmd
alias ll='ls -alF'
alias la='ls -A'
alias l='ls -CF'
alias read-permissions="stat --format '%a'"

# use already compiled lazygit
if ! which lazygit &>/dev/null && [ -f "/users_home/cmcc/am09320/bin/lazygit" ]; then
    alias lazygit="/users_home/cmcc/am09320/bin/lazygit"
fi

# Change accounts
alias @="switch_user"

# Conda
alias @c="conda activate"
alias @d="conda deactivate"

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# GoLang
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

PATH=$PATH:/users_home/cmcc/am09320/shared_lib/go/bin

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
    history -a        # write new lines
    history -n        # read new lines
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

# force the export of this function to remove any issue with `conda activate` command 
if which conda &>/dev/null; then
    export -f conda
    export -f __conda_exe
    export -f __conda_activate
    export -f __conda_reactivate
    export -f __conda_hashr
fi
