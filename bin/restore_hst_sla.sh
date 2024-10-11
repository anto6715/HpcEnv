#!/usr/bin/env bash

BASE_INPUT_DIR="/data/inputs/METOCEAN/historical/obs/ocean/satellite/CMS/Europe/altimetry/L3_EIS_202311/day"
SOURCE_DIR="/data/inputs/METOCEAN/rolling/obs/ocean/satellite/CMS/Europe/altimetry/L3_EIS_202311/day"
SOURCE_DATE="20240709"

SATELLITES=(
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
    2024
)
MONTHS=(
    6
    7
)

date_diff() {
    local reference_date=$1
    local compare_date=$2

    echo $((($(date -d "${reference_date} UTC" +%s) - $(date -d "${compare_date} UTC" +%s))/86400))
}

get_month_length() {
    local year="${1}"
    local month="${2}"
    date -d "${year}-$((month + 1))-01 - 1 day" +%d
}

main() {
    local sat year month day input_dir sat_filename sat_file month_length
    for sat in "${SATELLITES[@]}"; do
        echo "Sat ${sat}"
        for year in "${YEARS[@]}"; do
            echo "Year: ${year}"
            for month in "${MONTHS[@]}"; do
                echo "Month ${month}"

                month_length=$(get_month_length "${year}" "${month}")

                for day in $(seq "${month_length}"); do

                    local month_formatted=$(printf "%02d" $month)
                    local day_formatted=$(printf "%02d" $day)
                    for freq in 1hz 5hz; do
                        input_dir="${BASE_INPUT_DIR}/${sat}/${year}/${month_formatted}"
                        [ -d "${input_dir}" ] || continue
                        sat_filename="nrt_europe_*_phy_l3_${freq}_${year}${month_formatted}${day_formatted}_????????.nc"
                        sat_file=$(find "${input_dir}" -name "${sat_filename}")

                        if [ -z "${sat_file}" ]; then
                            local input_source_dir="${SOURCE_DIR}/${sat}/${SOURCE_DATE}"
                            local source_sat_file; source_sat_file=$(find "${input_source_dir}" -name "${sat_filename}" | head -n1)
                            if  [ -n "${source_sat_file}" ]; then
                                echo "Missing: ${sat_filename}"
                                echo "cp ${source_sat_file} ${input_dir}"
                            fi
                        fi
                    done
                done
            done
        done
    done
}

main "${@}"
