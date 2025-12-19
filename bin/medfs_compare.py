#!/bin/bash

reference_dir="/work/opa/mfs-dev/medfs/assw_EAS8_v1_4/EXP00/20200102/"
compare_dir1="/work/opa/am09320/dev/medfs/fix_EAS8_longrun/EXP00_part1/20200102"


preprocessing_dirs=("sst/out" "lobc/out" "wind/out" "runoff/out")
prepobs="prepobs/prepobs2nemo/work/"
nemo="model"


conda activate myenv4

echo "**************** Checking Pre-processing"
#for prep_dir in "${preprocessing_dirs[@]}"; do
#	compare.py ${reference_dir}/${prep_dir} ${compare_dir1}/${prep_dir}
#done
#
#compare.py ${reference_dir}/${prepobs} ${compare_dir1}/${prepobs} --name NC
compare.py ${reference_dir}/${nemo} ${compare_dir1}/${nemo} --name "_grid_"
compare.py ${reference_dir}/prepobs ${compare_dir1}/${nemo} --name "_grid_"

echo "**************** Checking NEMO"
#echo compare.py ${reference_dir}/${nemo} ${compare_dir1}/${nemo} --name "_grid_"
