#! /usr/bin/env bash

################################################################################
#
# Common template to start a bash development
#
# MM YYYY
# NAME SURNAME (email)
#
################################################################################


########################
#
# BASH SETTINGS
#
########################
set -o errexit  # abort on nonzero exitstatus
set -o nounset  # abort on unbound variable
set -o pipefail # don't hide errors within pipes


########################
#
# VARIABLES
#
########################
script_name=$(basename "${0}")
script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
readonly script_name script_dir


########################
#
# FUNCTIONS
#
########################
main() {
    check_args "${@}"
    # do stuff here
}

#+++ Functions
usage() {
    cat 2>&1 <<HELPMSG

    Usage:  $0 [OPTIONS] [ARGUMENTS]
    Options:
        -h, --help          Print this help message

HELPMSG
    exit 1
}

check_args() {
    if [[ ! "${#}" -eq 1 && ! "${#}" -eq 2 ]]; then
        usage
    fi
}
#---

main "${@}"
