#!/bin/bash

install_mamba() {
    curl -L -O "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh"
    bash Miniforge3-$(uname)-$(uname -m).sh
}

myw() {
    local usr; usr=$(whoami)
    [ "${HPC_SYSTEM}" == "juno" ] && cd "/work/cmcc/${usr}"
    [ "${HPC_SYSTEM}" == "zeus" ] && cd "/work/opa/${usr}"

    # default local pc
    cd /work/antonio
}

myd() {
    local usr; usr=$(whoami)
    [ "${HPC_SYSTEM}" == "juno" ] && cd "/data/cmcc/${usr}"
    [ "${HPC_SYSTEM}" == "zeus" ] && cd "/data/opa/${usr}"
    echo 1>&2 "No data partition available"
}

tui_an() {
    local bulletin_day="${1:?"Missing bulletin day: Usage: tui_an <bulletin_day>"}"
    cylc tui "nrt_eas/b${bulletin_day}"
}

tui_fc() {
    local bulletin_day="${1:?"Missing bulletin day: Usage: tui_fc <bulletin_day>"}"
    cylc tui "nrt_efs/b${bulletin_day}"
}
