#!/bin/bash

# bash cmd
alias ll='ls -alF'
alias la='ls -A'
alias l='ls -CF'

# accounts
alias mfs="switch_user mfs"
alias mfs-dev="switch_user mfs-dev"
alias das="switch_user das"
alias zeus_cylc="ssh -L 8082:localhost:8082 am09320@zeus01.cmcc.scc"
alias guu="git fetch && git pull"

# conda/mamba envs
## set mamba as default
alias conda="mamba"
alias ccylc="conda activate myenvcylc_v0.1"
alias cbase="conda activate base"
alias cenv="conda activate myenv5_v0.1"
