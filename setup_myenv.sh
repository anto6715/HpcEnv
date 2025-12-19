#!/bin/bash

TO_LOAD=("bash_settings" "bash_aliases" "bash_functions" "bash_mamba")
setup_script_dir=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

for to_load in "${TO_LOAD[@]}"; do
    # shellcheck source=.
    . "${setup_script_dir}/${to_load}"
done

export PATH="${setup_script_dir}/bin:${PATH}"
