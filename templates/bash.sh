#! /usr/bin/env bash

#
# Author: Antonio Mariani
#
#% Common template to start a bash development
#


#+++ Bash settings
set -o errexit  # abort on nonzero exitstatus
set -o nounset  # abort on unbound variable
set -o pipefail # don't hide errors within pipes
#---

#+++ Variables
script_name=$(basename "${0}")
script_dir=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
readonly script_name script_dir
#---

main() {
    check_args "${@}"
    # do stuff here
}

#+++ Functions
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
#---

main "${@}"
