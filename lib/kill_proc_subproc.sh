#!/bin/bash

rootPid="$1"

_listDescendantsPid () {
    local rootPid="$1"
    local children=$(ps -o pid= --ppid "${rootPid}")

    for pid in ${children}; do
        _listDescendantsPid "$pid"
    done

    echo "$children"
}

for pid in $(_listDescendantsPid "${rootPid}"); do
    echo "Killing process with pid: ${pid}"
    kill -9 "${pid}"
done

echo "Killing root process with pid: ${rootPid}"
kill -9 "${rootPid}"
