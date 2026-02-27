#!/usr/bin/env bash

# Move between partitions
if [ "${HPC_SYSTEM:-}" == "juno" ]; then
    alias myw='cd /work/cmcc/$USER'
    alias myd='cd /data/cmcc/$USER'
fi

# bash cmd
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

