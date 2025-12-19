#!/bin/bash

myArray=("/work/oda/ag15419/arc_link/simu_river_ctrl/output" "/work/oda/ag15419/arc_link/simu_river_po/output" )
day=20201011


for i in ${!myArray[@]}; do
	pathToSearch=${myArray[$i]}
	templateToSearch="*1d*_${day}_grid_T.nc*"

	echo "Analyzing path: ${pathToSearch}"
	file_a[$i]=$(find -L ${pathToSearch} -name "${templateToSearch}" | tail -1)
done

echo

for i in ${!myArray[@]}; do
	echo "element $i is ${file_a[$i]}"
done
