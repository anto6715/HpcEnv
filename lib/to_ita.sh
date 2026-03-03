#!/bin/bash

set -o errexit

dst="Stagione 07"

mkdir -p "$dst"

for f in *S07*; do

    ffmpeg -i "$f" -map 0:v -map 0:a:m:language:ita -sn -c copy "$dst/$f"
done
