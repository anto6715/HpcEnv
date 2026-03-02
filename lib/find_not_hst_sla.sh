#!/usr/bin/env bash

BASE_DIR="/data/inputs/METOCEAN/historical/obs/ocean/satellite/CMS/Europe/altimetry/L3/day"
SATELITES=(
    AltiKa
    Cryosat-2
    Envisat
    ERS1
    ERS2
    GFO
    HY-2A
    HY-2B
    Jason-1
    Jason-2
    Jason-3
    Sentinel-3A
    Sentinel-3B
    Sentinel-6A
    TOPEX
)

YEARS=(
    2023
)
MONTHS=(
    10
)

date_diff() {
    local reference_date=$1
    local compare_date=$2

    echo $((($(date -d "${reference_date} UTC" +%s) - $(date -d "${compare_date} UTC" +%s))/86400))
}

main() {
    for sat in "${SATELITES[@]}"; do
        for year in "${YEARS[@]}"; do
            for month in "${MONTHS[@]}"; do
                input_dir="${BASE_DIR}/${sat}/${year}/${month}"
                for sat_file in "${input_dir}/"*.nc; do
                    filename=$(basename "${sat_file}")
                    fdate_pdate=$(echo "${filename}" | grep -oP "\d{8}_\d{8}")
                    bdate="${fdate_pdate:0:8}"
                    pdate="${fdate_pdate:9:8}"
                    n_days=$(date_diff "${pdate}" "${bdate}")
                    if [[ "${n_days}" -lt 21 ]]; then
                        echo 1>&2 "WRONG SLA file: ${sat_file}"
                    else
                        echo 1>&2 "CORRECT SLA file: ${sat_file}"
                    fi
                done
            done
        done
    done
}

main "${@}"
