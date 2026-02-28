#!/usr/bin/env bash

# Lazygit
alias lg="lazygit"

# Move between partitions
if [ "${HPC_SYSTEM:-}" == "juno" ]; then
    alias myw='cd /work/cmcc/$USER'
    alias myd='cd /data/cmcc/$USER'
fi

# Bash cmd
alias ll='ls -alF'
alias la='ls -A'
alias l='ls -CF'
alias read-permissions="stat --format '%a'"

if [ -x /usr/bin/dircolors ]; then
    alias ls='ls --color=auto'

    alias grep='grep --color=auto'
    alias fgrep='fgrep --color=auto'
    alias egrep='egrep --color=auto'
fi

# Kerberos
alias kinit_otp='kinit -n;kinit -T FILE:/tmp/krb5cc_`id -u`'

# Change accounts
alias @="switch_user"

# Conda
alias @c="conda activate"
alias @d="conda deactivate"

# Git
alias g='git'
alias ga='git add'
alias gf='git fetch'
alias gs='git status'
alias gss='git status -s'
alias gl='git pull'
alias gb='git branch '
alias gbr='git branch -r'
alias gd='git diff'
alias gco='git checkout '
alias gcob='git checkout -b '
alias gre='git remote'
alias gres='git remote show'
alias glgg='git log --graph --max-count=5 --decorate --pretty="oneline"'
alias gm='git merge'
alias gp='git push'
alias gpo='git push origin'
alias ggpush='git push origin $(current_branch)'
alias gc='git commit -v'
alias gcm='git commit -m'
alias gcmnv='git commit --no-verify -m'
alias gcanenv='git commit --amend --no-edit --no-verify'
