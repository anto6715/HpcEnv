#!/bin/bash

g100_account=$1
zeus_path=$2
g100_path=$3

rsync -av -e "ssh -i ~/.ssh/asus_zeus" "${zeus_path}" "${g100_account}"@login.g100.cineca.it:"${g100_path}"
