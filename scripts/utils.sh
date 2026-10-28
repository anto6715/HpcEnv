#!/bin/bash

restore_xtrace="false"
if [[ $- == *x* ]]; then
    set +x
    restore_xtrace="true"
fi

# Color definition using tput (no colors when there is no terminal, e.g. TERM unset)
default_color=$(tput sgr 0 2>/dev/null)
red="$(tput setaf 1 2>/dev/null)"
yellow="$(tput setaf 3 2>/dev/null)"
green="$(tput setaf 2 2>/dev/null)"
blue="$(tput setaf 4 2>/dev/null)"

# Light log functions
info() {
    printf "%s==> %s%s\n" "$blue" "$1" "$default_color"
}

success() {
    printf "%s==> %s%s\n" "$green" "$1" "$default_color"
}

error() {
    printf "%s==> %s%s\n" "$red" "$1" "$default_color"
}

warning() {
    printf "%s==> %s%s\n" "$yellow" "$1" "$default_color"
}

# Machine profile used by install.sh and symlinks.sh: "juno" on the cluster
# (HPC_SYSTEM=juno, or a hostname containing juno), "laptop" anywhere else.
detect_profile() {
    if [[ "${HPC_SYSTEM:-}" == "juno" || "$(hostname)" == *juno* ]]; then
        echo "juno"
    else
        echo "laptop"
    fi
}

if [[ $restore_xtrace == "true" ]]; then
    set -x
fi
