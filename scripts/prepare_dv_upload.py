#!/usr/bin/env python3
"""Prepare the MDS DV (interface verification) test upload of MEDSEA_ANALYSISFORECAST_PHY_006_013, release 202611.

Creates <dest>/<dataset_id>/ for each dataset and copies two files in it:
- the same two keys (<date>, bulletin, an/fc) for every non-monthly dataset, taken from the production dir;
- the two most recent months common to all monthly datasets, from the monthly dir (default: production dir);
- the static dataset is the exception: all MED-MFC_006_013_*.nc files of the static dir.

File names: <date>_<freq>-CMCC--<file_type>-MFSeas11-MEDATL-b<bdate>_<an|fc>-sv<version>.nc
Dataset map from ODPL medsea-prod_124/dataset_spec.json (vault: CMEMS/MEDSEA_ANALYSISFORECAST_PHY_006_013_202611.csv).
"""

import re
import shutil
import sys

from argparse import Namespace
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple


TAG = "202611"
STATIC_DATASET = f"cmems_mod_med_phy_anfc_4.2km_static_{TAG}"
STATIC_PATTERN = "MED-MFC_006_013_*.nc"

# dataset_id (without tag) -> (freq, file_type)
DATASETS = {
    "cmems_mod_med_phy-cur_anfc_4.2km_P1D-m": ("d", "RFVL"),
    "cmems_mod_med_phy-cur_anfc_4.2km_P1M-m": ("m", "RFVL"),
    "cmems_mod_med_phy-cur_anfc_4.2km_PT15M-i": ("qm", "RFVL"),
    "cmems_mod_med_phy-cur_anfc_4.2km-2D_PT1H-m": ("2dh", "RFVL"),
    "cmems_mod_med_phy-cur_anfc_4.2km-3D_PT1H-m": ("3dh", "RFVL"),
    "cmems_mod_med_phy-cur_anfc_detided-4.2km_P1D-m": ("d", "HCNT"),
    "cmems_mod_med_phy-mld_anfc_4.2km_P1D-m": ("d", "AMXL"),
    "cmems_mod_med_phy-mld_anfc_4.2km_P1M-m": ("m", "AMXL"),
    "cmems_mod_med_phy-mld_anfc_4.2km-2D_PT1H-m": ("2dh", "AMXL"),
    "cmems_mod_med_phy-sal_anfc_4.2km_P1D-m": ("d", "PSAL"),
    "cmems_mod_med_phy-sal_anfc_4.2km_P1M-m": ("m", "PSAL"),
    "cmems_mod_med_phy-sal_anfc_4.2km-2D_PT1H-m": ("2dh", "PSAL"),
    "cmems_mod_med_phy-sal_anfc_4.2km-3D_PT1H-m": ("3dh", "PSAL"),
    "cmems_mod_med_phy-ssh_anfc_4.2km_P1D-m": ("d", "ASLV"),
    "cmems_mod_med_phy-ssh_anfc_4.2km_P1M-m": ("m", "ASLV"),
    "cmems_mod_med_phy-ssh_anfc_4.2km_PT15M-i": ("qm", "ASLV"),
    "cmems_mod_med_phy-ssh_anfc_4.2km-2D_PT1H-m": ("2dh", "ASLV"),
    "cmems_mod_med_phy-ssh_anfc_detided-4.2km_P1D-m": ("d", "SHNT"),
    "cmems_mod_med_phy-temp_anfc_4.2km_P1D-m": ("d", "TEMP"),
    "cmems_mod_med_phy-temp_anfc_4.2km_P1M-m": ("m", "TEMP"),
    "cmems_mod_med_phy-temp_anfc_4.2km-2D_PT1H-m": ("2dh", "TEMP"),
    "cmems_mod_med_phy-temp_anfc_4.2km-3D_PT1H-m": ("3dh", "TEMP"),
    "cmems_mod_med_phy-wcur_anfc_4.2km_P1D-m": ("d", "LRZA"),
    "cmems_mod_med_phy-wcur_anfc_4.2km_P1M-m": ("m", "LRZA"),
}
MONTHLY_FREQ = "m"
N_FILES = 2

FILE_RE = re.compile(
    r"^(?P<date>\d{6,8})_(?P<freq>[0-9a-z]+)-CMCC--(?P<type>[A-Z]{4})-MFSeas11-MEDATL"
    r"-b(?P<bdate>\d{8})_(?P<kind>an|fc)-sv[0-9.]+\.nc$"
)

# (date, bdate, kind), e.g. ("20251215", "20251216", "an")
Key = Tuple[str, str, str]


def get_args(raw_args=None) -> Namespace:
    import argparse

    parse = argparse.ArgumentParser(
        description="Prepare the MDS DV test upload: one folder per dataset, two files each"
    )
    parse.add_argument("static_dir", type=Path, help=f"Dir with the static files ({STATIC_PATTERN})")
    parse.add_argument("prod_dir", type=Path, help="Production dir, searched recursively for *.nc")
    parse.add_argument("dest", type=Path, help="Destination root; <dest>/<dataset_id>/ is created")
    parse.add_argument("-m", "--monthly-dir", type=Path, help="Dir with the monthly (_m-) files (default: prod_dir)")
    parse.add_argument(
        "-k",
        "--keys",
        nargs=N_FILES,
        metavar="DATE_bBDATE_KIND",
        help="Force the non-monthly keys, e.g. 20251215_b20251216_an 20251216_b20251216_fc",
    )
    parse.add_argument("-n", "--dry-run", action="store_true", help="Print what would be copied, copy nothing")

    return parse.parse_args(raw_args)


def log(level: str, msg: str):
    print(f"[{level}] {msg}", flush=True)


def scan(name: str, root: Path, freqs: set) -> Dict[Tuple[str, str], Dict[Key, Path]]:
    """Index the files of the given frequencies under root: (freq, file_type) -> key -> path."""
    index = defaultdict(dict)
    n_nc, n_used, other, unparsed = 0, 0, defaultdict(int), []
    for path in sorted(root.rglob("*.nc")):
        n_nc += 1
        m = FILE_RE.match(path.name)
        if not m:
            unparsed.append(path.name)
            continue
        if (m["freq"], m["type"]) not in DATASETS.values():
            other[f"{m['freq']}-{m['type']}"] += 1
            continue
        if m["freq"] not in freqs:
            continue
        key = (m["date"], m["bdate"], m["kind"])
        files = index[(m["freq"], m["type"])]
        if key in files:
            log("WARN", f"duplicate {path}: using {files[key]}")
            continue
        files[key] = path
        n_used += 1
    log("INFO", f"{name} scan of {root}: {n_nc} .nc files, {n_used} used")
    if other:
        log("INFO", "  ignored (not a DV dataset): " + ", ".join(f"{k} {n}" for k, n in sorted(other.items())))
    if unparsed:
        log("WARN", f"  {len(unparsed)} names not matching {FILE_RE.pattern}, e.g. {', '.join(unparsed[:3])}")
    return index


def key_str(key: Key) -> str:
    return f"{key[0]}_b{key[1]}_{key[2]}"


def select(name: str, datasets: List[str], index, forced: List[str] = None) -> Tuple[List[Key], str]:
    """Pick N_FILES keys present in all the datasets: the most recent ones, or the forced ones.

    Returns (keys, error); error is empty when the selection is valid.
    """
    sets = {ds: set(index.get(DATASETS[ds], {})) for ds in datasets}
    common = set.intersection(*sets.values())
    log("INFO", f"{name}: {len(common)} keys common to all {len(datasets)} datasets")
    for ds, s in sets.items():
        span = f"{key_str(min(s))} .. {key_str(max(s))}" if s else "-"
        log("INFO" if s else "WARN", f"  {ds}: {len(s)} files ({span})")
    if forced:
        keys = [tuple(re.fullmatch(r"(\d+)_b(\d{8})_(an|fc)", k).groups()) for k in forced]
        missing = [key_str(k) for k in keys if k not in common]
        if missing:
            return [], f"{name}: forced keys not available in all datasets: {' '.join(missing)}"
        return keys, ""
    if len(common) < N_FILES:
        return [], f"{name}: {len(common)} keys common to all datasets, {N_FILES} needed"
    # most recent bulletin first, then most recent date, analysis before forecast
    return sorted(common, key=lambda k: (k[1], k[0], k[2] == "an"), reverse=True)[:N_FILES], ""


def copy(src: Path, dest_dir: Path, dry_run: bool) -> bool:
    """Copy src into dest_dir unless already there; True if copied (or would be)."""
    target = dest_dir / src.name
    if target.exists():
        log("SKIP", f"  exists: {target}")
        return False
    log("DRY" if dry_run else "COPY", f"  {src} -> {dest_dir}/")
    if not dry_run:
        dest_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, target)
    return True


def main(raw_args: List["str"] = None):
    args = get_args(raw_args)
    monthly_dir = args.monthly_dir or args.prod_dir
    log("INFO", f"Mode: {'DRY-RUN, nothing is copied' if args.dry_run else 'COPY'}")
    log("INFO", f"static={args.static_dir} prod={args.prod_dir} monthly={monthly_dir} dest={args.dest}")
    for d in (args.static_dir, args.prod_dir, monthly_dir):
        if not d.is_dir():
            log("ERROR", f"not a directory: {d}")
            sys.exit(1)

    errors = []
    statics = sorted(args.static_dir.glob(STATIC_PATTERN))
    log("INFO", f"{args.static_dir}: {len(statics)} static files ({STATIC_PATTERN})")
    if not statics:
        errors.append(f"static: no {STATIC_PATTERN} in {args.static_dir}")

    daily = [ds for ds, (freq, _) in DATASETS.items() if freq != MONTHLY_FREQ]
    monthly = [ds for ds, (freq, _) in DATASETS.items() if freq == MONTHLY_FREQ]
    index = scan("non-monthly", args.prod_dir, {DATASETS[ds][0] for ds in daily})
    m_index = scan("monthly", monthly_dir, {MONTHLY_FREQ})
    groups = []
    for name, datasets, idx, forced in (("non-monthly", daily, index, args.keys), ("monthly", monthly, m_index, None)):
        keys, error = select(name, datasets, idx, forced)
        if error:
            errors.append(error)
            continue
        log("INFO", f"{name}: selected keys {' '.join(key_str(k) for k in keys)}")
        groups.append((datasets, idx, keys))

    if errors and not args.dry_run:
        for e in errors:
            log("ERROR", e)
        log("ERROR", "nothing copied; run with -n to see the plan")
        sys.exit(1)

    n_copied = n_skipped = 0
    plan = [(STATIC_DATASET, statics)] + [
        (f"{ds}_{TAG}", [idx[DATASETS[ds]][k] for k in keys]) for datasets, idx, keys in groups for ds in datasets
    ]
    for folder, sources in plan:
        log("INFO", f"{folder} ({len(sources)} files)")
        for src in sources:
            if copy(src, args.dest / folder, args.dry_run):
                n_copied += 1
            else:
                n_skipped += 1

    verb = "to copy" if args.dry_run else "copied"
    log("INFO", f"Summary: {len(plan)} folders, {n_copied} files {verb}, {n_skipped} already present")
    for e in errors:
        log("ERROR", e)
    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
