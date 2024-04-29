#!/bin/bash

cmd=$1
inputFile=$2

while read -r line ; do
   eval "${cmd} ${line}" 
done < ${inputFile}