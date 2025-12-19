#!/bin/bash

if [ "$#" != 3 ]; then
    echo "Usage: $0 <src> <dest> <username>"
fi

src=$1
dst=$2
username=$3

hostname=login.g100.cineca.it

rsync -a -e "ssh -i ~/.ssh/asus_zeus" "${username}@${hostname}":${src} "${dst}" --progress --copy-links
