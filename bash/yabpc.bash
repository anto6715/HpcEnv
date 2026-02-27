# see yabpc color declaration
__prompt_color__="Cyan"

function yabpc() {
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
        "${debian_chroot:+($debian_chroot)}${Title}${Bold}${!__prompt_color__}\u@\h${Reset} \w"
    )

    ## Git
    [ "$(git rev-parse --is-inside-work-tree 2>/dev/null)" == "true" ] && {
        declare SegmentGit="${Green}[" \
                git_status="" \
                git_status_ahead="" \
                git_status_behind="" \
                git_status_mod="" \
                git_status_untracked="" \
                git_status_tobecommitted="" \
                git_status_del=""
        SegmentGit+="$(__git_ps1 | tr -d '( )')"
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
        Segments+=("${Cyan}${Bold}git:${Reset}$SegmentGit] ${Reset}")
    }

    ## Python venv
    [ -n "${VIRTUAL_ENV+x}" ] && {
        Segments+=("${Cyan}${Bold}${Invert} $(basename "$VIRTUAL_ENV") ${Reset}")
    }
    ## Conda
    [ -n "${CONDA_PROMPT_MODIFIER+x}" ] && {
        # add it to the beginning of the promptstring
        Segments=("${Green}(${CONDA_PROMPT_MODIFIER//[\(\) ]/})${Reset}" "${Segments[@]}")
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
