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


def scan(root: Path, freqs: set) -> Dict[Tuple[str, str], Dict[Key, Path]]:
    """Index the files under root: (freq, file_type) -> key -> path."""
    index = defaultdict(dict)
    for path in sorted(root.rglob("*.nc")):
        m = FILE_RE.match(path.name)
        if not m or m["freq"] not in freqs:
            continue
        key = (m["date"], m["bdate"], m["kind"])
        files = index[(m["freq"], m["type"])]
        if key in files:
            print(f"WARNING: duplicate {path.name}: using {files[key]}", file=sys.stderr)
            continue
        files[key] = path
    return index


def key_str(key: Key) -> str:
    return f"{key[0]}_b{key[1]}_{key[2]}"


def select(datasets: List[str], index, forced: List[str] = None) -> List[Key]:
    """Pick N_FILES keys present in all the datasets: the most recent ones, or the forced ones."""
    sets = {ds: set(index.get(DATASETS[ds], {})) for ds in datasets}
    common = set.intersection(*sets.values())
    if forced:
        keys = [tuple(re.fullmatch(r"(\d+)_b(\d{8})_(an|fc)", k).groups()) for k in forced]
        missing = [key_str(k) for k in keys if k not in common]
        if missing:
            raise SystemExit(f"ERROR: keys not available in all datasets: {' '.join(missing)}")
        return keys
    if len(common) < N_FILES:
        counts = "\n".join(f"  {ds}: {len(s)} files" for ds, s in sets.items())
        raise SystemExit(f"ERROR: {len(common)} keys common to all datasets, {N_FILES} needed\n{counts}")
    # most recent bulletin first, then most recent date, analysis before forecast
    return sorted(common, key=lambda k: (k[1], k[0], k[2] == "an"), reverse=True)[:N_FILES]


def copy(src: Path, dest_dir: Path, dry_run: bool):
    target = dest_dir / src.name
    if target.exists():
        print(f"  exists, skipped: {target}")
        return
    print(f"  {src} -> {dest_dir}/")
    if not dry_run:
        dest_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, target)


def main(raw_args: List["str"] = None):
    args = get_args(raw_args)
    monthly_dir = args.monthly_dir or args.prod_dir
    for d in (args.static_dir, args.prod_dir, monthly_dir):
        if not d.is_dir():
            raise SystemExit(f"ERROR: not a directory: {d}")

    statics = sorted(args.static_dir.glob(STATIC_PATTERN))
    if not statics:
        raise SystemExit(f"ERROR: no {STATIC_PATTERN} in {args.static_dir}")

    daily = [ds for ds, (freq, _) in DATASETS.items() if freq != MONTHLY_FREQ]
    monthly = [ds for ds, (freq, _) in DATASETS.items() if freq == MONTHLY_FREQ]
    index = scan(args.prod_dir, {DATASETS[ds][0] for ds in daily})
    m_index = scan(monthly_dir, {MONTHLY_FREQ})
    keys = select(daily, index, args.keys)
    m_keys = select(monthly, m_index)
    print(f"Keys: {' '.join(key_str(k) for k in keys)}")
    print(f"Monthly keys: {' '.join(key_str(k) for k in m_keys)}")

    print(f"{STATIC_DATASET} ({len(statics)} files)")
    for src in statics:
        copy(src, args.dest / STATIC_DATASET, args.dry_run)
    for datasets, idx, sel in ((daily, index, keys), (monthly, m_index, m_keys)):
        for ds in datasets:
            print(f"{ds}_{TAG}")
            for key in sel:
                copy(idx[DATASETS[ds]][key], args.dest / f"{ds}_{TAG}", args.dry_run)


if __name__ == "__main__":
    main()
