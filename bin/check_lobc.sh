#!/bin/bash

dir1=$1
dir2=$2

check_var() {
	var_to_check=$1
	./min_max4.py $dir1/$filename $dir2/$filename $var_to_check $var_to_check
}

for file in $dir1/*_merc.nc; do

	filename=$(basename $file)
	typeFile=$(echo $filename | cut -d_ -f 3)
	if [[ _$typeFile == _"TS" ]]; then
		check_var "votemper"
		check_var "vosaline"
		continue
	elif [[ $typeFile == "U" ]]; then
		check_var "vozocrtx"
		continue
	elif [[ $typeFile == "V" ]]; then
		check_var "vomecrty"
		continue
	fi
done