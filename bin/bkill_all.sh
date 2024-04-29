#!/bin/bash

jobInExecution="$(bjobs)"

# print bjobs stdout, with tail remove the header, with awk select the first column
jobIdList="$(echo "${jobInExecution}" | tail -n +2 | awk '{print $1}')"

for jobId in ${jobIdList}; do
	echo "Killing ${jobId}"
	bkill ${jobId}
done
