#!/bin/bash

# bash cmd
alias ll='ls -alF'
alias la='ls -A'
alias l='ls -CF'
alias get_chmod="stat --format '%a'"

# accounts
alias mfs="switch_user mfs"
alias mfs-dev="switch_user mfs-dev"
alias das="switch_user das"
alias med_inter="switch_user med_inter"
alias adrinemobfm="switch_user adrinemobfm"
alias zeus_cylc="ssh -L 8082:localhost:8082 am09320@zeus01.cmcc.scc"
alias guu="git fetch && git pull"

# conda/mamba envs
## set mamba as default
alias ccylc="mamba activate myenvcylc_v0.2"
alias cbase="mamba activate base"
alias cenv="mamba activate myenv5_v0.1"
