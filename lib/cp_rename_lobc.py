#!/usr/bin/env python

import sys
from pathlib import Path

MONTH = ["08", "09", "10", "11", "12"]


def main():
    try:
        input_dir = Path(sys.argv[1]).resolve()
        output_dir = Path(sys.argv[2]).resolve()
        old_year = str(sys.argv[3])
        new_year = str(sys.argv[4])
    except IndexError:
        print("Usage: ./cp_rename_lobc.py <input_dir> <output_dir> <new_year>")
        exit(1)

    input_files = []
    for month in MONTH:
        input_files.extend(
            [f for f in input_dir.glob(f"mfs_bdy*_y{old_year}m{month}d*.nc")]
        )
    for f in sorted(input_files):
        filename = f.name
        new_filename = filename.replace(old_year, new_year)
        new_file = output_dir / new_filename
        print(f"ln -s {f.as_posix()} {new_file}")

        try:
            new_file.symlink_to(f)
        except FileExistsError as e:
            print(e)


if __name__ == "__main__":
    main()
