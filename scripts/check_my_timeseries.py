#!/usr/bin/env python3
import fnmatch
import re

from collections import namedtuple
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

from mds import mds_s3


TIME_RANGE = namedtuple("TimeRange", ["start", "end"])

DATASET_PATTERN = {
    "cmems_mod_med_phy-cur_my_4.2km_P1D-m": "*_d-*RFVL-MFSe3r1*-MED*nc",
    "cmems_mod_med_phy-cur_my_4.2km_P1M-m": "*_m-*RFVL-MFSe3r1*-MED*nc",
    "cmems_mod_med_phy-cur_my_4.2km_P1Y-m": "*_y-*RFVL-MFSe3r1*-MED*nc",
    "cmems_mod_med_phy-cur_my_4.2km_PT1H-m": "*_h-*RFVL-MFSe3r1*-MED*nc",
    "cmems_mod_med_phy-mld_my_4.2km_P1D-m": "*_d-*AMXL-MFSe3r1*-MED*nc",
    "cmems_mod_med_phy-mld_my_4.2km_P1M-m": "*_m-*AMXL-MFSe3r1*-MED*nc",
    "cmems_mod_med_phy-mld_my_4.2km_P1Y-m": "*_y-*AMXL-MFSe3r1*-MED*nc",
    "cmems_mod_med_phy-sal_my_4.2km_P1D-m": "*_d-*PSAL-MFSe3r1*-MED*nc",
    "cmems_mod_med_phy-sal_my_4.2km_P1M-m": "*_m-*PSAL-MFSe3r1*-MED*nc",
    "cmems_mod_med_phy-sal_my_4.2km_P1Y-m": "*_y-*PSAL-MFSe3r1*-MED*nc",
    "cmems_mod_med_phy-ssh_my_4.2km_P1D-m": "*_d-*ASLV-MFSe3r1*-MED*nc",
    "cmems_mod_med_phy-ssh_my_4.2km_P1M-m": "*_m-*ASLV-MFSe3r1*-MED*nc",
    "cmems_mod_med_phy-ssh_my_4.2km_P1Y-m": "*_y-*ASLV-MFSe3r1*-MED*nc",
    "cmems_mod_med_phy-ssh_my_4.2km_PT1H-m": "*_h-*ASLV-MFSe3r1*-MED*nc",
    "cmems_mod_med_phy-tem_my_4.2km_P1Y-m": "*_y-*TEMP-MFSe3r1*-MED*nc",
    "cmems_mod_med_phy-temp_my_4.2km_P1D-m": "*_d-*TEMP-MFSe3r1*-MED*nc",
    "cmems_mod_med_phy-temp_my_4.2km_P1M-m": "*_m-*TEMP-MFSe3r1*-MED*nc",
}
MY_TIME_RANGE = TIME_RANGE(start=datetime(2023, 6, 1), end=datetime(2026, 7, 31))


DATASET_PATTERN_REA_ONLY = {
    "cmems_mod_med_phy-hflux_my_4.2km_P1D-m": "*_d-*HFLX-MFSe3r1*-MED*nc",
    "cmems_mod_med_phy-hflux_my_4.2km_P1M-m": "*_m-*HFLX-MFSe3r1*-MED*nc",
    "cmems_mod_med_phy-mflux_my_4.2km_P1D-m": "*_d-*MFLX-MFSe3r1*-MED*nc",
    "cmems_mod_med_phy-mflux_my_4.2km_P1M-m": "*_m-*MFLX-MFSe3r1*-MED*nc",
    "cmems_mod_med_phy-wflux_my_4.2km_P1D-m": "*_d-*WFLX-MFSe3r1*-MED*nc",
    "cmems_mod_med_phy-wflux_my_4.2km_P1M-m": "*_m-*WFLX-MFSe3r1*-MED*nc",
}
REA_ONLY_TIME_RANGE = TIME_RANGE(start=datetime(2023, 6, 1), end=datetime(2025, 7, 31))

# MDS
BUCKET = "mdl-native-12"
# PRODUCT = "MEDSEA_ANALYSISFORECAST_PHY_006_013"
PRODUCT = "MEDSEA_MULTIYEAR_PHY_006_004"
# Load everything
TAG = None
DATASET_ID = None


def load_files_from_mds() -> List[str]:
    """Download list of files from mds"""
    ########################
    s3_files = mds_s3.get_file_list(
        s3_bucket=BUCKET,
        product=PRODUCT,
        dataset_id=DATASET_ID,
        dataset_version=TAG,
        file_filter="*",
        recursive=True,
        subdir=None,
    )
    if not s3_files:
        raise ValueError("No files found in MDS - bucket: {}, product: {}".format(BUCKET, PRODUCT))

    s3_filenames = list()
    for s3f in s3_files:
        s3_filenames.append(Path(s3f.file).name)

    return s3_filenames


def file_in_time_range(file_name: str, time_range: TIME_RANGE) -> bool:
    file_date = file_name[0:8]
    try:
        file_datetime = datetime.strptime(file_date, "%Y%m%d")
    except ValueError:
        return False
    return time_range.start <= file_datetime <= time_range.end


def dataset_frequency(dataset: str) -> str:
    """Return the frequency (P1D, P1M, P1Y, PT1H) encoded in the dataset id."""
    match = re.search(r"_(P1D|P1M|P1Y|PT1H)-m$", dataset)
    if not match:
        raise ValueError(f"Cannot infer frequency from dataset id: {dataset}")
    return match.group(1)


def expected_timestamps(time_range: TIME_RANGE, frequency: str) -> List[str]:
    """Return the file timestamps (YYYYMMDD) expected in the given time range.

    P1D and PT1H datasets ship one file per day; P1Y files are only expected
    for years fully contained in the time range.
    """
    timestamps = []

    if frequency in ("P1D", "PT1H"):
        day = time_range.start.date()
        while day <= time_range.end.date():
            timestamps.append(day.strftime("%Y%m%d"))
            day += timedelta(days=1)
    elif frequency == "P1M":
        current = datetime(time_range.start.year, time_range.start.month, 1)
        while current <= time_range.end:
            if current >= time_range.start:
                timestamps.append(current.strftime("%Y%m%d"))
            if current.month == 12:
                current = datetime(current.year + 1, 1, 1)
            else:
                current = datetime(current.year, current.month + 1, 1)
    elif frequency == "P1Y":
        for year in range(time_range.start.year, time_range.end.year + 1):
            if datetime(year, 1, 1) >= time_range.start and datetime(year, 12, 31) <= time_range.end:
                timestamps.append(datetime(year, 1, 1).strftime("%Y%m%d"))
    else:
        raise ValueError(f"Unknown frequency: {frequency}")

    return timestamps


def find_timeseries_holes(files: List[str], time_range: TIME_RANGE, frequency: str) -> List[str]:
    """Return the expected timestamps with no corresponding file (holes in the timeseries)."""
    present = {f[:8] for f in files}
    return [t for t in expected_timestamps(time_range, frequency) if t not in present]


def find_duplicate_files(files: List[str]) -> Dict[str, List[str]]:
    """Return files sharing the same date, frequency and type (e.g. 20230601_d-TEMP)."""
    groups: Dict[str, List[str]] = {}
    for f in files:
        match = re.match(r"^(\d{8})_([hdmy])-(?:\w+--)?([A-Z0-9]+)-", f)
        if match:
            key = f"{match.group(1)}_{match.group(2)}-{match.group(3)}"
            groups.setdefault(key, []).append(f)
    return {key: group for key, group in groups.items() if len(group) > 1}


def report_dataset(dataset: str, files: List[str], time_range: TIME_RANGE, label: str = "files") -> None:
    """Print per-dataset file count, timeseries holes and duplicates."""
    
    holes = find_timeseries_holes(files, time_range, dataset_frequency(dataset))
    duplicates = find_duplicate_files(files)
    print(f"Dataset: {dataset}, {label}: {len(files)}, time range: {time_range}, holes: {len(holes)}, duplicates: {len(duplicates)}")
    if holes:
        print(f"  Missing timestamps: {', '.join(holes)}")
    for key, group in sorted(duplicates.items()):
        print(f"  Duplicate {key}:")
        for f in sorted(group):
            print(f"    {f}")


def main():
    print("Loading files from MDS...")
    files_on_mds = load_files_from_mds()
    print(f"Found {len(files_on_mds)} files on MDS.")
    print("Filtering files by time range...")

    my_files_on_mds = [f for f in files_on_mds if file_in_time_range(f, MY_TIME_RANGE)]
    rea_only_files_on_mds = [f for f in files_on_mds if file_in_time_range(f, REA_ONLY_TIME_RANGE)]
    print(
        f"Found {len(my_files_on_mds)} files in my time range and {len(rea_only_files_on_mds)} files in read-only time range."
    )

    for dataset, pattern in DATASET_PATTERN.items():
        this_dataset_files = [f for f in my_files_on_mds if fnmatch.fnmatch(f, pattern)]
        report_dataset(dataset, this_dataset_files, MY_TIME_RANGE)
    for dataset, pattern in DATASET_PATTERN_REA_ONLY.items():
        this_dataset_rea_only_files = [f for f in rea_only_files_on_mds if fnmatch.fnmatch(f, pattern)]
        report_dataset(dataset, this_dataset_rea_only_files, REA_ONLY_TIME_RANGE, label="read-only files")


if __name__ == "__main__":
    main()
