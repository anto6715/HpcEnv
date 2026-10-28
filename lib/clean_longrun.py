#!/usr/bin/env python3
"""Clean the files of a longrun that are not useful any more.

For each day folder <root>/YYYYMMDD with start <= YYYYMMDD <= end (both included), removes the matches of PATTERNS:
- nemo_ww/*out_*
- nemo_ww/*1ts*
- oceanvar/corr*

Dry-run by default: lists what would be removed, with sizes and a summary per pattern. Pass --apply to remove.
A match that is a folder is removed with its content (like rm -rf); a symlink is removed, never its target.
"""

import os
import re
import shutil
import sys

from argparse import Namespace
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple


# (sub-folder of the day folder, glob pattern)
PATTERNS = [
    ("nemo_ww", "*out_*"),
    ("nemo_ww", "*1ts*"),
    ("oceanvar", "corr*"),
]
DAY_RE = re.compile(r"^\d{8}$")


def yyyymmdd(value: str) -> str:
    """argparse type: a valid YYYYMMDD date, kept as a string (8 digits compare like dates)."""
    if not DAY_RE.match(value):
        raise ValueError(value)
    datetime.strptime(value, "%Y%m%d")
    return value


def get_args(raw_args=None) -> Namespace:
    import argparse

    parse = argparse.ArgumentParser(
        description="Clean the not-useful files of a longrun (dry-run by default, --apply to remove)"
    )
    parse.add_argument("root", type=Path, help="Longrun root, the folder with the YYYYMMDD day folders")
    parse.add_argument("start", type=yyyymmdd, help="First day to clean, YYYYMMDD (included)")
    parse.add_argument("end", type=yyyymmdd, help="Last day to clean, YYYYMMDD (included)")
    parse.add_argument("--apply", action="store_true", help="Really remove the files (default: only list them)")

    return parse.parse_args(raw_args)


def log(level: str, msg: str):
    print(f"[{level}] {msg}", flush=True)


def human(size: float) -> str:
    for unit in ("B", "KiB", "MiB", "GiB"):
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TiB"


def day_folders(root: Path, start: str, end: str) -> List[Path]:
    """Day folders <root>/YYYYMMDD with start <= YYYYMMDD <= end, sorted by date."""
    return sorted(p for p in root.iterdir() if DAY_RE.match(p.name) and start <= p.name <= end and p.is_dir())


def find(day: Path) -> List[Tuple[str, Path]]:
    """(pattern label, path) of the matches in a day folder; a path matching more patterns is listed once."""
    found = {}
    for sub, pattern in PATTERNS:
        folder = day / sub
        if folder.is_dir():
            for path in sorted(folder.glob(pattern)):
                found.setdefault(path, f"{sub}/{pattern}")
    return [(label, path) for path, label in found.items()]


def size_of(path: Path) -> int:
    """Apparent size of a file, or of a folder with its content; symlinks are not followed."""
    if path.is_symlink() or not path.is_dir():
        return path.lstat().st_size
    total = 0
    for dirpath, dirnames, filenames in os.walk(path):
        total += sum(os.lstat(os.path.join(dirpath, name)).st_size for name in dirnames + filenames)
    return total


def remove(path: Path):
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    else:
        path.unlink()


def main(raw_args: Optional[List[str]] = None):
    args = get_args(raw_args)
    root = args.root.absolute()
    if args.start > args.end:
        log("ERROR", f"start {args.start} is after end {args.end}")
        sys.exit(1)
    if not root.is_dir():
        log("ERROR", f"{root} is not a folder")
        sys.exit(1)

    mode = "APPLY, files are removed" if args.apply else "DRY-RUN, nothing is removed (--apply to remove)"
    log("INFO", f"Mode: {mode}")
    days = day_folders(root, args.start, args.end)
    log("INFO", f"{len(days)} day folders from {args.start} to {args.end} in {root}")

    count = defaultdict(int)
    size = defaultdict(int)
    errors = 0
    for day in days:
        for label, path in find(day):
            try:
                nbytes = size_of(path)
                if args.apply:
                    remove(path)
            except OSError as err:
                log("ERROR", f"{path}: {err}")
                errors += 1
                continue
            log("RM" if args.apply else "DRY", f"{path.relative_to(root)} ({human(nbytes)})")
            count[label] += 1
            size[label] += nbytes

    verb = "removed" if args.apply else "to remove"
    for sub, pattern in PATTERNS:
        label = f"{sub}/{pattern}"
        log("INFO", f"{label:<16} {count[label]:>7} {verb}, {human(size[label])}")
    log("INFO", f"{'total':<16} {sum(count.values()):>7} {verb}, {human(sum(size.values()))}")
    if errors:
        log("ERROR", f"{errors} paths not removed, see above")
        sys.exit(1)


if __name__ == "__main__":
    main()
