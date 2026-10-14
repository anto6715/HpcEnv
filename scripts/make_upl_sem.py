#!/usr/bin/env python3
"""Create UPL semaphore files, one per frequency, listing the files to upload.

Input files are matched by name, e.g.
    20251101_m-CMCC--AMXL-MFSeas11-MEDATL-b20260611_an-sv12.00.fake.nc
where the token between the leading date and the first '-' ('m' here,
'2dh' in '..._2dh-...') is the frequency.

For each frequency found, writes in the output dir
    UPL--<freq>-<YYYYMMDD>_<YYYYMMDD>T<hhmmss>Z.txt
holding the absolute paths of that frequency's files, one per line, sorted.
Both dates come from the current UTC time, taken once per run.

Usage: make_upl_sem.py <input_dir> <output_dir>
"""
import argparse
import os
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone

FILE_RE = re.compile(r"^\d{8}_(?P<freq>[A-Za-z0-9]+)-.+\.nc$")


def group_by_freq(input_dir):
    """Return {freq: [absolute paths]} for the matching files in input_dir."""
    groups = defaultdict(list)
    for name in os.listdir(input_dir):
        path = os.path.join(input_dir, name)
        match = FILE_RE.match(name)
        if match and os.path.isfile(path):
            groups[match.group("freq")].append(path)
    return groups


def write_sem(output_dir, freq, paths, now):
    """Write the semaphore for one frequency and return its path."""
    name = "UPL--{}-{}_{}Z.txt".format(
        freq, now.strftime("%Y%m%d"), now.strftime("%Y%m%dT%H%M%S"))
    final = os.path.join(output_dir, name)
    tmp = os.path.join(output_dir, "." + name + ".tmp")
    with open(tmp, "w") as f:
        f.writelines(path + "\n" for path in sorted(paths))
    # Rename at the end so a watcher never picks up a half-written file.
    os.replace(tmp, final)
    return final


def main():
    parser = argparse.ArgumentParser(
        description="Create one UPL semaphore per frequency in output_dir, "
                    "listing the matching files of input_dir.")
    parser.add_argument("input_dir", help="directory holding the files to list")
    parser.add_argument("output_dir", help="directory where the semaphores go")
    args = parser.parse_args()

    input_dir = os.path.abspath(args.input_dir)
    output_dir = os.path.abspath(args.output_dir)
    for directory in (input_dir, output_dir):
        if not os.path.isdir(directory):
            sys.exit("error: not a directory: {}".format(directory))

    groups = group_by_freq(input_dir)
    if not groups:
        sys.exit("error: no matching files in {}".format(input_dir))

    now = datetime.now(timezone.utc)
    for freq in sorted(groups):
        sem = write_sem(output_dir, freq, groups[freq], now)
        print("{} ({} files)".format(sem, len(groups[freq])))


if __name__ == "__main__":
    main()
