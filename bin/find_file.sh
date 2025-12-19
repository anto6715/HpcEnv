#!/bin/bash

path=$1
file=$2

eval "find ${path} -name ${file}"
