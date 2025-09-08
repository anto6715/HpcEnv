#!/bin/bash

################################################################################
#
# Archive LOBC from OcFlow structure to allout/output-LOBC
#
# 09 2025
# Antonio Mariani (antonio.mariani@cmcc.it)
#
################################################################################

#!/bin/bash

INPUT_BASE_DIR="/work/cmcc/am09320/MedFS_EAS10/lobc"
DST_BASE_DIR="/data/cmcc/mfs/MFS_EAS9/allout/output-LOBC"


for bulletin_dir in "$INPUT_BASE_DIR/b"????????"_lobc"; do
    bulletin_dirname=$(basename $bulletin_dir)
    bulletin="${bulletin_dirname:1:8}"
    echo "$bulletin"

    bulletin_dst_dir="$DST_BASE_DIR/$bulletin"
    mkdir -p "$bulletin_dst_dir"

    for cycle_point_dir in "$bulletin_dir/"????????; do
        echo -e "\t $cycle_point_dir"

        cycle_point=$(basename $cycle_point_dir)

        out_dir="$bulletin_dst_dir/$cycle_point"
        mkdir -p "$out_dir"

        for f in "$cycle_point_dir/lobc/out/"*".nc"; do
            echo cp "$f" "$out_dir"
            cp "$f" "$out_dir"
        done
    done
done

