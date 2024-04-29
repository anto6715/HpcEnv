#!/bin/bash

path=$1
string=$2

eval "grep --color=always -nrw ${path} -e ${string}"
