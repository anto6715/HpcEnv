#!/bin/bash

install_mamba() {
    curl -L -O "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh"
    bash Miniforge3-$(uname)-$(uname -m).sh
}
export -f install_mamba

function myw() {
    local usr
    usr=$(whoami)
    local work_path

    if [ "${HPC_SYSTEM}" == "juno" ]; then
        work_path="/work/cmcc/${usr}"
    elif [ "${HPC_SYSTEM}" == "zeus" ]; then
        work_path="/work/opa/${usr}"
    else
        work_path=/work/antonio
    fi

    # default local pc
    if [ -d "${work_path}" ]; then
        cd "${work_path}"
    else
        echo 1>&2 "Path doesn't exist: '${work_path}'"
    fi
}
export -f myw

function myd() {
    local usr
    usr=$(whoami)
    local data_path

    if [ "${HPC_SYSTEM}" == "juno" ]; then
        data_path="/data/cmcc/${usr}"
    elif [ "${HPC_SYSTEM}" == "zeus" ]; then
        data_path="/data/opa/${usr}"
    else
        echo 1>&2 "No data partition available"
        return
    fi

    # default local pc
    if [ -d "${data_path}" ]; then
        cd "${data_path}"
    else
        echo 1>&2 "Path doesn't exist: '${data_path}'"
    fi
}
export -f myd

function tui_an() {
    local bulletin_day="${1:?"Missing bulletin day: Usage: tui_an <bulletin_day>"}"
    cylc tui "nrt_eas/b${bulletin_day}"
}
export -f tui_an

function tui_fc() {
    local bulletin_day="${1:?"Missing bulletin day: Usage: tui_fc <bulletin_day>"}"
    cylc tui "nrt_efs/b${bulletin_day}"
}
export -f tui_fc

function 2fa_juno() {
    local otp_token; otp_token=$(pass cmcc/juno/authenticator)
    local second_fact; second_fact=$(oathtool --totp=SHA1 -b "${otp_token}")

    echo "${second_fact}" | xclip -selection clipboard
    echo "Copied OTP code to clipboard. Will clear in 45 seconds."

    sleep 45
    echo -n | xclip -selection clipboard
}
export -f twofa_juno
#brequeue -e # se fallit
#brequeue
