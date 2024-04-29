#!/bin/bash

TO_LOAD=("bash_settings" "bash_aliases" "bash_functions" "bash_mamba")
script_dir=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

for to_load in "${TO_LOAD[@]}"; do
    # shellcheck source=.
    . "${script_dir}/${to_load}"
done

export PATH="${script_dir}/bin:${PATH}"
