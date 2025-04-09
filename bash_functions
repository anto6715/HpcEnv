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

    (sleep 45 && echo -n | xclip -selection clipboard &)

}
export -f 2fa_juno

bjobs_stats() {
    local user="${1:-"$(whoami)"}"
    bjobs -a -o "jobid stat job_name run_time start_time exec_host" -u "${user}" |sort
}
export -f bjobs_stats

function yabpc()
{
    declare  ExitCode="$?"
    ## Title (see Ubuntu's .bashrc file)
    declare     Title="\001\e]2;${debian_chroot:+($debian_chroot)}\u@\h: \w\a\002"
    ## Formatting
    declare     Blink="\001\e[5m\002"
    declare      Bold="\001\e[1m\002"
    declare       Dim="\001\e[2m\002"
    declare    Hidden="\001\e[8m\002"
    declare    Invert="\001\e[7m\002"
    declare    Italic="\001\e[3m\002"
    declare     Reset="\001\e[0m\002"
    # declare ResetBold="\001\e[21m\002"
    declare ResetBold="\\033[2m"
    declare    Strike="\001\e[9m\002"
    declare Underline="\001\e[4m\002"
    ## Colors
    declare     Black="\001\e[30m\002"
    declare      Blue="\001\e[34m\002"
    declare      Cyan="\001\e[36m\002"
    declare  DarkGray="\001\e[90m\002"
    declare     Green="\001\e[32m\002"
    declare LightCyan="\001\e[96m\002"
    declare LightGray="\001\e[37m\002"
    declare   Magenta="\001\e[35m\002"
    declare       Red="\001\e[31m\002"
    declare     White="\001\e[97m\002"
    declare    Yellow="\001\e[33m\002"
    ## Symbols
    declare     Cloud=$'\uf0c2'
    declare DevPython=$'\ue235'
    declare      Edit=$'\uf044'
    declare     Error=$'\ue009'
    declare    Folder=$'\ue5fe'
    declare       Git=$'\uf1d3'
    declare GitBranch=$'\ue725'
    declare       New=$'\uf893'
    declare      Plus=$'\uf067'
    declare    Python=$'\uf820'
    declare   VertBar=$'\u2503'
    declare   Warning=$'\uf071'
    declare   YinYang=$'\ufb7e'
    ## Segments
    declare  Segments=(
        # "${White}${Bold}\w${Reset}"
        "${debian_chroot:+($debian_chroot)}\[\033[01;32m\]\u@\h\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]"
    )

    ## Git
    [ "$(git rev-parse --is-inside-work-tree 2>/dev/null)" == "true" ] && {
        declare SegmentGit="${Blue}${Bold}${Invert}" \
                git_status="" \
                git_status_ahead="" \
                git_status_behind="" \
                git_status_mod="" \
                git_status_untracked="" \
                git_status_tobecommitted="" \
                git_status_del=""
        SegmentGit+=" $(__git_ps1 | tr -d '( )')"
        git_status="$(git status --porcelain --branch)"
        git_status_ahead="$(grep -o -E 'ahead [0-9]+' <<< "$git_status")"
        git_status_behind="$(grep -o -E 'behind [0-9]+' <<< "$git_status")"
        git_status_mod="$(grep -c -E '^[ MTARC]M' <<< "$git_status")"
        git_status_untracked="$(grep -c -E '^\?\?' <<< "$git_status")"
        git_status_del="$(grep -c -E '^[ MTARC]D' <<< "$git_status")"
        git_status_tobecommitted="$(grep -c -E '^[MTARCD]' <<< "$git_status")"
        [ "$git_status_tobecommitted" -gt "0" ] &&
            SegmentGit+="*"
        [ -n "$git_status_behind" ] &&
            SegmentGit+="[-${git_status_behind//[!0-9]/}]"
        [ -n "$git_status_ahead" ] &&
            SegmentGit+="[+${git_status_ahead//[!0-9]/}]"
        [ "$git_status_untracked" -gt "0" ] &&
            SegmentGit+=" ?${git_status_untracked}"
        [ "$git_status_mod" -gt "0" ] &&
            SegmentGit+=" M${git_status_mod}"
        [ "$git_status_del" -gt "0" ] &&
            SegmentGit+=" D${git_status_del}"
        Segments+=("$SegmentGit ${Reset}")
    }

    ## Python venv
    [ -n "${VIRTUAL_ENV+x}" ] && {
        Segments+=("${Cyan}${Bold}${Invert} $(basename "$VIRTUAL_ENV") ${Reset}")
    }

    ## Conda
    [ -n "${CONDA_PROMPT_MODIFIER+x}" ] && {
        Segments+=("${Cyan}${Bold}${Invert} ${CONDA_PROMPT_MODIFIER//[\(\) ]/} ${Reset}")
    }

    PS1="$Title"
    if [ "$ExitCode" -ne "0" ]; then
        PS1+="${Red}${Bold}${Invert} exit code $ExitCode $Reset\n\n"
    else
        PS1+="\n"
    fi
    PS1+="${Segments[*]}\n"
    PS1+="${Bold}\$${Reset} "

    PS2="  "
}
export -f yabpc
#brequeue -e # se fallit
#brequeue
