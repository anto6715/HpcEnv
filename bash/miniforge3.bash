MAMBA_ROOT_PREFIX="$HOME/.miniforge3"

__conda_setup="$('$MAMBA_ROOT_PREFIX/bin/conda' 'shell.bash' 'hook' 2> /dev/null)"
if [ $? -eq 0 ]; then
    eval "$__conda_setup"
else
    if [ -f "$MAMBA_ROOT_PREFIX/etc/profile.d/conda.sh" ]; then
        . "$MAMBA_ROOT_PREFIX/etc/profile.d/conda.sh"
    else
        export PATH="$MAMBA_ROOT_PREFIX/bin:$PATH"
    fi
fi
unset __conda_setup

if [ -f "$MAMBA_ROOT_PREFIX/etc/profile.d/mamba.sh" ]; then
    . "$MAMBA_ROOT_PREFIX/etc/profile.d/mamba.sh"
fi

# <<< conda initialize <<<

# Force the export of these functions to remove any issue with `conda activate`
# in subshells. Kept in this file (not in custom.bash) so it stays self-contained
# and can be dropped as-is into accounts that aren't fully configured.
# Use `command -v` (not `which`): conda is a shell function the hook defines,
# which an external `which` cannot see.
if command -v conda &>/dev/null; then
    export -f conda
    export -f __conda_exe
    export -f __conda_activate
    export -f __conda_reactivate
    export -f __conda_hashr
fi
