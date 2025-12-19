#!/bin/bash

inputFile="$1"
oldpattern=$2
newpattern=$3

for file in ./${inputFile}; do
	echo $file
	eval "sed -i 's+${oldpattern}+${newpattern}+g' $file"
done
