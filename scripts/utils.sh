#!/bin/bash

restore_xtrace="false"
if [[ $- == *x* ]]; then
    set +x
    restore_xtrace="true"
fi

# Color definition using tput
default_color=$(tput sgr 0)
red="$(tput setaf 1)"
yellow="$(tput setaf 3)"
green="$(tput setaf 2)"
blue="$(tput setaf 4)"

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

if [[ $restore_xtrace == "true" ]]; then
    set -x
fi
