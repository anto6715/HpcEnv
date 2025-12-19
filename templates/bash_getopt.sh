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
script_dir=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
readonly script_name script_dir


########################
#
# FUNCTIONS
#
########################
main() {
    local parsed_arguments
    parsed_arguments=$(getopt -o h --long help -- "$@") || usage

    eval set -- "${parsed_arguments}"
    while :; do
        case "$1" in
            -h | --help) usage ;;
            --) shift; break ;; # -- means the end of the arguments; drop this, and break out of the while loop
            *)
                printf "Unexpected option: %s\n" "${1}";  usage ;;
        esac
        shift
    done
    check_args "${@}"
    # do stuff here
}

usage() {
    cat 2>&1 << HELPMSG

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

main "${@}"
