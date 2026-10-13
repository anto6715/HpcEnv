#!/usr/bin/env python3
"""Clean the restarts of a BLK (BSFS EAS9) longrun that are not needed any more.

NEMO at day D reads its restarts from <root>/restart/<D-1>T2400 (RESTART_IN_DIR), the folder filled by the NEMO
task of the previous cycle point: a run can start again at day D only while that folder is complete.

Kept days, never touched: the last day of each month, and the last --keep-last days found in root (default 3).
For each other day YYYYMMDD with start <= YYYYMMDD <= end (both included), removes the matches of PATTERNS:
- restart/YYYYMMDDT2400: *_restart_*.nc (ocean and ice), restart_*.ww3, r_ww3_*.nc, r_nemo_*.nc
- YYYYMMDD/analysis (link to the Cylc work dir of the NEMO task): *_restart_*.nc, restart.ww3, restart001.ww3,
  r_ww3.nc, r_nemo.nc and the restart_NNNN.nc / restart_ice_NNNN.nc links to the input restarts
The increments (corr_*.nc, ANINCR.NC) and every other file are left.

A run written by the July 2026 code has every file of restart/ hard-linked to the Cylc work dir: the space comes back
only when all the names of a file are removed. The summary gives the space really freed and the files that still
have another name elsewhere.

Dry-run by default: lists what would be removed, per day and pattern, with a summary. Pass --apply to remove.
A symlink is removed, never its target.
"""

import calendar
import re
import sys

from argparse import Namespace
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


# (folder relative to root, {day} = YYYYMMDD; glob pattern)
PATTERNS = [
    ("restart/{day}T2400", "*_restart_*.nc"),
    ("restart/{day}T2400", "restart_*.ww3"),
    ("restart/{day}T2400", "r_ww3_*.nc"),
    ("restart/{day}T2400", "r_nemo_*.nc"),
    ("{day}/analysis", "*_restart_*.nc"),
    ("{day}/analysis", "restart_[0-9][0-9][0-9][0-9].nc"),
    ("{day}/analysis", "restart_ice_[0-9][0-9][0-9][0-9].nc"),
    ("{day}/analysis", "restart.ww3"),
    ("{day}/analysis", "restart001.ww3"),
    ("{day}/analysis", "r_ww3.nc"),
    ("{day}/analysis", "r_nemo.nc"),
]
DAY_RE = re.compile(r"^\d{8}$")
RESTART_DIR_RE = re.compile(r"^(\d{8})T2400$")


def is_date(value: str) -> bool:
    try:
        datetime.strptime(value, "%Y%m%d")
    except ValueError:
        return False
    return True


def yyyymmdd(value: str) -> str:
    """argparse type: a valid YYYYMMDD date, kept as a string (8 digits compare like dates)."""
    if not DAY_RE.match(value) or not is_date(value):
        raise ValueError(value)
    return value


def non_negative(value: str) -> int:
    """argparse type: an integer >= 0."""
    number = int(value)
    if number < 0:
        raise ValueError(value)
    return number


def get_args(raw_args=None) -> Namespace:
    import argparse

    parse = argparse.ArgumentParser(
        description="Clean the restarts of a BLK longrun, keeping month-ends (dry-run by default, --apply to remove)"
    )
    parse.add_argument("root", type=Path, help="Longrun root (EXP_WORK_DIR), the folder with restart/ and YYYYMMDD/")
    parse.add_argument("start", type=yyyymmdd, help="First day to clean, YYYYMMDD (included)")
    parse.add_argument("end", type=yyyymmdd, help="Last day to clean, YYYYMMDD (included)")
    parse.add_argument(
        "--keep-last",
        type=non_negative,
        default=3,
        help="Also keep the last N days found in root (default: 3)",
    )
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


def label_of(folder: str, pattern: str) -> str:
    return f"{folder.format(day='YYYYMMDD')}/{pattern}"


def is_month_end(day: str) -> bool:
    date = datetime.strptime(day, "%Y%m%d")
    return date.day == calendar.monthrange(date.year, date.month)[1]


def all_days(root: Path) -> List[str]:
    """Days with a day folder <root>/YYYYMMDD or a restart folder <root>/restart/YYYYMMDDT2400, sorted."""
    days = {p.name for p in root.iterdir() if DAY_RE.match(p.name) and is_date(p.name) and p.is_dir()}
    restart_root = root / "restart"
    if restart_root.is_dir():
        for path in restart_root.iterdir():
            match = RESTART_DIR_RE.match(path.name)
            if match and is_date(match.group(1)) and path.is_dir():
                days.add(match.group(1))
    return sorted(days)


def keep_reason(day: str, last_days: Set[str], keep_last: int) -> Optional[str]:
    if is_month_end(day):
        return "month-end"
    if day in last_days:
        return f"one of the last {keep_last} days"
    return None


def find(root: Path, day: str) -> List[Tuple[str, Path]]:
    """(pattern label, path) of the matches of a day; a path matching more patterns is listed once."""
    found = {}
    for folder, pattern in PATTERNS:
        path_dir = root / folder.format(day=day)
        if path_dir.is_dir():
            for path in sorted(path_dir.glob(pattern)):
                found.setdefault(path, label_of(folder, pattern))
    return [(label, path) for path, label in found.items()]


def main(raw_args: Optional[List[str]] = None):
    args = get_args(raw_args)
    root = args.root.absolute()
    if args.start > args.end:
        log("ERROR", f"start {args.start} is after end {args.end}")
        sys.exit(1)
    if not root.is_dir():
        log("ERROR", f"{root} is not a folder")
        sys.exit(1)
    if not (root / "restart").is_dir():
        log("WARN", f"{root / 'restart'} not found: only the day folders are cleaned")

    mode = "APPLY, files are removed" if args.apply else "DRY-RUN, nothing is removed (--apply to remove)"
    log("INFO", f"Mode: {mode}")
    found_days = all_days(root)
    last_days = set(found_days[-args.keep_last :]) if args.keep_last else set()
    days = [day for day in found_days if args.start <= day <= args.end]
    log("INFO", f"{len(days)} days from {args.start} to {args.end} in {root}")
    if last_days:
        log("INFO", f"Last {args.keep_last} days in root, always kept: {', '.join(sorted(last_days))}")

    verb = "removed" if args.apply else "to remove"
    count = defaultdict(int)
    size = defaultdict(int)
    # (st_dev, st_ino) -> [hard links of the file, names removed, size]
    inodes: Dict[Tuple[int, int], List[int]] = {}
    errors = 0
    for day in days:
        reason = keep_reason(day, last_days, args.keep_last)
        if reason:
            log("KEEP", f"{day} ({reason})")
            if reason == "month-end" and not any((root / "restart" / f"{day}T2400").glob("*_restart_*.nc")):
                log("WARN", f"{day} is kept but restart/{day}T2400 has no NEMO restart")
            continue

        day_count = defaultdict(int)
        day_size = defaultdict(int)
        for label, path in find(root, day):
            try:
                stat = path.lstat()
                if args.apply:
                    path.unlink()
            except OSError as err:
                log("ERROR", f"{path}: {err}")
                errors += 1
                continue
            day_count[label] += 1
            day_size[label] += stat.st_size
            inode = inodes.setdefault((stat.st_dev, stat.st_ino), [stat.st_nlink, 0, stat.st_size])
            inode[1] += 1

        for label in day_count:
            log("RM" if args.apply else "DRY", f"{day} {label}: {day_count[label]} files, {human(day_size[label])}")
            count[label] += day_count[label]
            size[label] += day_size[label]

    for folder, pattern in PATTERNS:
        label = label_of(folder, pattern)
        log("INFO", f"{label:<52} {count[label]:>8} {verb}, {human(size[label])}")
    log("INFO", f"{'total':<52} {sum(count.values()):>8} {verb}, {human(sum(size.values()))}")

    freed = sum(nbytes for nlink, removed, nbytes in inodes.values() if removed >= nlink)
    linked = [nbytes for nlink, removed, nbytes in inodes.values() if removed < nlink]
    log("INFO", f"Space {'freed' if args.apply else 'to free'}: {human(freed)}")
    if linked:
        log(
            "WARN",
            f"{len(linked)} files ({human(sum(linked))}) still have another name outside the cleaned folders "
            "(hard links): their space is not freed",
        )
    if errors:
        log("ERROR", f"{errors} paths not removed, see above")
        sys.exit(1)


if __name__ == "__main__":
    main()
