#!/bin/bash

queue=$1
bsubCmd="$2"
logErr="aderr"$3
logOut="adout"$3
bsubArgs=$4


bsubOptions="-q ${queue} -P 0510 -e ${logErr} -o ${logOut}"

[ -n "${bsubArgs}" ] && bsubOptions="${bsubOptions} ${bsubArgs}"

bsub ${bsubOptions} "${bsubCmd}"
