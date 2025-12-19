#!/bin/bash

__prj_dir__=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )


# Source aliases
source "${__prj_dir__}/bash_aliases"

# Source functions
source "${__prj_dir__}/bash_functions"

# Update prompt
source "${__prj_dir__}/yabpc.bash"

# Add bin to the PATH
export PATH="$__prj_dir__/bin:${PATH}"
