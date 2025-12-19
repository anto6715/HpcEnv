#!/bin/bash

if [ ! "$#" == "3" ]; then
	echo "Usage: $? <source> <dest> <account>"
	exit 0
fi

hostname=zeus01.cmcc.scc

get_from_g100() {
    # double quote to avoid globe expansion here
    local src="$1"
    local dest=$2
    local accountName=$3

    rsync -a -e "ssh -i ~/.ssh/id_rsa" "${accountName}@${hostname}":${src} "${dest}" --progress --copy-links
}

