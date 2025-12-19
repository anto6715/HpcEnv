#!/usr/bin/env python3
"""
Generate delivery XML from NetCDF files in a directory.
Maps filenames to dataset names based on file type codes and frequency.

Usage: python generate_delivery_xml_from_files.py <path> [options]
Example: python generate_delivery_xml_from_files.py /data/cmcc/am09320/CMEMS/E3R1I/work/CMEMS_anfc_d/test/ -o delivery.xml
"""

import sys
import os
import hashlib
import re
from datetime import datetime
from pathlib import Path
from collections import defaultdict


# Dataset name mapping based on file type code and frequency
# Format: (file_type_code, frequency_code) -> (dataset_variable_name, dataset_frequency)
DATASET_MAPPING = {
    ("TEMP", "d"): ("temp", "P1D"),
    ("TEMP", "h"): ("temp", "PT1H"),
    ("TEMP", "y"): ("tem", "P1Y"),
    ("PSAL", "d"): ("sal", "P1D"),
    ("PSAL", "h"): ("sal", "PT1H"),
    ("PSAL", "y"): ("sal", "P1Y"),
    ("RFVL", "d"): ("cur", "P1D"),
    ("RFVL", "h"): ("cur", "PT1H"),
    ("RFVL", "y"): ("cur", "P1Y"),
    ("ASLV", "d"): ("ssh", "P1D"),
    ("ASLV", "h"): ("ssh", "PT1H"),
    ("ASLV", "y"): ("ssh", "P1Y"),
    ("AMXL", "d"): ("mld", "P1D"),
    ("AMXL", "h"): ("mld", "PT1H"),
    ("AMXL", "y"): ("mld", "P1Y"),
}


def calculate_md5(filepath):
    """Calculate MD5 checksum of a file."""
    md5_hash = hashlib.md5()
    try:
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                md5_hash.update(chunk)
        return md5_hash.hexdigest()
    except Exception as e:
        print(
            f"Warning: Could not calculate checksum for {filepath}: {e}",
            file=sys.stderr,
        )
        return ""


def parse_filename(filename):
    """
    Parse NetCDF filename to extract metadata.

    Example: 20250101_d-CMCC--TEMP-MFSe3r1i-MED-b20250207_in-sv01.00.nc
    Returns: {
        'date': '20250101',
        'freq': 'd',
        'type': 'TEMP',
        'model': 'MFSe3r1i',
        'bulletin': '20250207',
        'year': '2025',
        'month': '01'
    }
    """
    # Pattern: YYYYMMDD_F-CMCC--TYPE-MODEL-REGION-bYYYYMMDD_in-sv##.##.nc
    # More flexible pattern to handle variations
    pattern = r"(\d{8})_([dhqmy])-CMCC--([A-Z]{4})-(.+?)-([A-Z]+)-b(\d{8})_.+\.nc"
    match = re.match(pattern, filename)

    if not match:
        return None

    date_str, freq, file_type, model, region, bulletin = match.groups()

    return {
        "date": date_str,
        "freq": freq,
        "type": file_type,
        "model": model,
        "region": region,
        "bulletin": bulletin,
        "year": date_str[:4],
        "month": date_str[4:6],
    }


def get_dataset_name(file_type, freq, version="202511"):
    """
    Generate dataset name from file type and frequency.

    Format: cmems_mod_med_phy-{var}_my_4.2km_{freq}-m_{version}
    Example: cmems_mod_med_phy-temp_my_4.2km_P1D-m_202511
    """
    key = (file_type, freq)

    if key not in DATASET_MAPPING:
        return None

    var_name, dataset_freq = DATASET_MAPPING[key]

    return f"cmems_mod_med_phy-{var_name}_my_4.2km_{dataset_freq}-m_{version}"


def get_relative_path(filename, parsed_info):
    """
    Generate relative path for the file in the delivery structure.
    Format: YYYY/MM/filename
    Example: 2023/06/20230601_d-CMCC--TEMP-MFSe3r1i-MED-b20230707_in-sv01.00.nc
    """
    year = parsed_info["year"]
    month = parsed_info["month"]

    if "_y-CMCC" in filename:
        return filename
    return f"{year}/{month}/{filename}"


def scan_directory(path, calculate_checksums=False, version="202511"):
    """
    Scan directory for NetCDF files and organize by dataset.

    Returns: dict of {
        dataset_name: [
            {
                'filename': relative_path,
                'full_path': absolute_path,
                'checksum': md5_checksum
            },
            ...
        ]
    }
    """
    datasets = defaultdict(list)

    path_obj = Path(path)
    if not path_obj.exists():
        print(f"Error: Path {path} does not exist", file=sys.stderr)
        return datasets

    # Find all .nc files
    nc_files = list(path_obj.glob("*.nc"))

    if not nc_files:
        # Try recursive search
        nc_files = list(path_obj.rglob("*.nc"))

    print(f"Found {len(nc_files)} NetCDF files", file=sys.stderr)

    for nc_file in sorted(nc_files):
        filename = nc_file.name
        parsed_info = parse_filename(filename)

        if not parsed_info:
            print(f"Warning: Could not parse filename: {filename}", file=sys.stderr)
            continue

        dataset_name = get_dataset_name(
            parsed_info["type"], parsed_info["freq"], version
        )

        if not dataset_name:
            print(
                f"Warning: Unknown file type/frequency combination: {parsed_info['type']}/{parsed_info['freq']}",
                file=sys.stderr,
            )
            continue

        relative_path = get_relative_path(filename, parsed_info)

        file_info = {
            "filename": relative_path,
            "full_path": str(nc_file),
            "checksum": calculate_md5(str(nc_file)) if calculate_checksums else "",
            "parsed": parsed_info,
        }

        datasets[dataset_name].append(file_info)
        print(f"  {filename} -> {dataset_name}", file=sys.stderr)

    return datasets


def generate_timestamp():
    """Generate timestamp in format YYYYMMDDTHHMMSSz."""
    return datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")


def generate_xml(
    path,
    output_file=None,
    calculate_checksums=False,
    file_type="NRT",
    product="MEDSEA_MULTIYEAR_PHY_006_004",
    version="202511",
):
    """Generate the complete XML for files in the given path."""

    # Scan directory
    datasets = scan_directory(path, calculate_checksums, version)

    if not datasets:
        print("Error: No valid datasets found in the specified path", file=sys.stderr)
        return None

    # Generate XML
    delivery_date = generate_timestamp()

    xml_lines = [
        '<?xml version="1.0" ?>',
        f'<delivery product="{product}" PushingEntity="MED-CMCC-LECCE-IT" date="{delivery_date}">',
    ]

    # Generate datasets in sorted order
    for dataset_name in sorted(datasets.keys()):
        xml_lines.append(f'    <dataset DatasetName="{dataset_name}">')

        for file_info in datasets[dataset_name]:
            start_time = generate_timestamp()
            stop_time = generate_timestamp()

            checksum = file_info["checksum"]
            filename = file_info["filename"]

            xml_lines.append(
                f'        <file FileName="{filename}" '
                f'StartUploadTime="{start_time}" '
                f'StopUploadTime="{stop_time}" '
                f'Checksum="{checksum}" '
                f'FileType="{file_type}" '
                f'FinalStatus="Delivered"/>'
            )

        xml_lines.append("    </dataset>")

    xml_lines.append("</delivery>")

    xml_content = "\n".join(xml_lines)

    if output_file:
        with open(output_file, "w") as f:
            f.write(xml_content)
        print(f"\nXML file generated: {output_file}", file=sys.stderr)
    else:
        print(xml_content)

    return xml_content


def main():
    if len(sys.argv) < 2:
        print("Usage: python generate_delivery_xml_from_files.py <path> [options]")
        print("\nOptions:")
        print("  -o, --output FILE     Output XML file (default: print to stdout)")
        print("  --checksum            Calculate MD5 checksums (slow for large files)")
        print("  --file-type TYPE      Set FileType attribute (default: NRT)")
        print(
            "  --product PRODUCT     Set product name (default: MEDSEA_MULTIYEAR_PHY_006_004)"
        )
        print("  --version VERSION     Set dataset version (default: 202511)")
        print("\nExample:")
        print(
            "  python generate_delivery_xml_from_files.py /data/path/to/files/ -o delivery.xml"
        )
        print(
            "  python generate_delivery_xml_from_files.py /data/path/to/files/ --checksum --file-type MY"
        )
        sys.exit(1)

    path = sys.argv[1]
    output_file = None
    calculate_checksums = False
    file_type = "NRT"
    product = "MEDSEA_MULTIYEAR_PHY_006_004"
    version = "202511"

    # Parse arguments
    i = 2
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg in ["-o", "--output"]:
            i += 1
            if i < len(sys.argv):
                output_file = sys.argv[i]
        elif arg == "--checksum":
            calculate_checksums = True
        elif arg == "--file-type":
            i += 1
            if i < len(sys.argv):
                file_type = sys.argv[i]
        elif arg == "--product":
            i += 1
            if i < len(sys.argv):
                product = sys.argv[i]
        elif arg == "--version":
            i += 1
            if i < len(sys.argv):
                version = sys.argv[i]
        i += 1

    if not os.path.exists(path):
        print(f"Error: Path '{path}' does not exist", file=sys.stderr)
        sys.exit(1)

    generate_xml(path, output_file, calculate_checksums, file_type, product, version)


if __name__ == "__main__":
    main()
