#!/bin/bash

################################################################################
#
# Find input file used in NRT cycle
#
# 09 2025
# Antonio Mariani (antonio.mariani@cmcc.it)
#
################################################################################


set -o errexit
set -o nounset

BASE_INPUT_DIR="/work/cmcc/mfs/cylc-run/nrt_easv9"
RUN_NAMES=(
    b20241029
    b20241105
    b20241112
    b20241119
    b20241126
    b20241203
    b20241210
    b20241217
    b20241224
    b20241231
    # b20250107
    # b20250114
    # b20250121
    # b20250128
    # b20250204
    # b20250211
    # b20250218
    # b20250225
    # b20250304
    # b20250311
    # b20250318
    # b20250325
    # b20250401
    # b20250408
    # b20250415
    # b20250422
    # b20250429
    # b20250506
    # b20250513
    # b20250520
    # b20250527
    # b20250603
    # b20250610
    # b20250617
    # b20250624
    # b20250701
    # b20250708
    # b20250715
    # b20250722
    # b20250729
    # b20250805
    # b20250812
    # b20250819
    # b20250826
    # b20250902
)
DEST_DIR="/work/cmcc/mfs/input-LOBC"

declare run_name=""
declare cycle_point_log=""
declare cycle_point=""
declare base_dst_dir=""
declare out_dir=""
declare log_file=""
declare input_file=""

# ITERATE OVER CYLC RUNS
for run_name in "${RUN_NAMES[@]}"; do
    echo "Processing: $run_name"
    base_dst_dir="$DEST_DIR/$run_name"
    input_dir="$BASE_INPUT_DIR/$run_name/log/job"

    # ITERATE OVER CYCLE POINTS OF PRODUCTION
    for cycle_point_log in "$input_dir/"????????"T0000Z"; do
        log_file="$cycle_point_log/lobc/NN/job.err"

        # extract cycle point
        cycle_point="$(basename "$cycle_point_log")"
        cycle_point="${cycle_point:0:8}"

        # generate output dir for each cycle point
        out_dir="$base_dst_dir/$cycle_point"
        mkdir -p $out_dir

        echo -e "\tCycle point: $cycle_point"

        for f in $(grep -P "\+ original_lobc_file=" $log_file | tr -d "+"); do
            input_file=$(echo $f | cut -d"=" -f 2)
            echo -e "\t\tln -s $input_file -> $out_dir"
            if ! ln -s "$input_file" "$out_dir"; then
                echo "WARNING Already exists: $out_dir/$(basename $input_file)"
            fi
        done

    done
done
