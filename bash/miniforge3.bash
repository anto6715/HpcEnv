__base_conda_path__="$HOME/.miniforge3"

__conda_setup="$('$__base_conda_path__/bin/conda' 'shell.bash' 'hook' 2> /dev/null)"
if [ $? -eq 0 ]; then
    eval "$__conda_setup"
else
    if [ -f "$__base_conda_path__/etc/profile.d/conda.sh" ]; then
        . "$__base_conda_path__/etc/profile.d/conda.sh"
    else
        export PATH="$__base_conda_path__/bin:$PATH"
    fi
fi
unset __conda_setup

if [ -f "$__base_conda_path__/etc/profile.d/mamba.sh" ]; then
    . "$__base_conda_path__/etc/profile.d/mamba.sh"
fi

# <<< conda initialize <<<
# 
# Fix error related to the conda usage
export -f conda
export -f __conda_exe
export -f __conda_activate
export -f __conda_reactivate
export -f __conda_hashr
