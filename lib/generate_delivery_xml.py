#!/usr/bin/env python3
"""
Generate delivery XML for a given month.
Usage: python generate_delivery_xml.py YYYY MM [output_file.xml]
Example: python generate_delivery_xml.py 2023 01 delivery_2023_01.xml
"""

import datetime
import sys
from calendar import monthrange

# Dataset configurations
DATASETS = {
    # "cmems_mod_med_phy-cur_anfc_4.2km-3D_PT1H-m_202511": {
    #     "freq": "PT1H",  # hourly - one file per day
    #     "pattern": "{year}/{month:02d}/{date}_3dh-CMCC--RFVL-MFSeas10-MEDATL-b20250531_an-sv11.00.nc"
    # },
    "cmems_mod_med_phy-cur_anfc_4.2km_P1D-m_202511": {
        "freq": "P1D",  # daily
        "pattern": "{year}/{month:02d}/{date}_d-CMCC--RFVL-MFSeas10-MEDATL-b20250531_an-sv11.00.nc",
    },
    "cmems_mod_med_phy-cur_anfc_4.2km_P1M-m_202511": {
        "freq": "P1M",  # monthly - one file per month
        "pattern": "{year}/{date}_m-CMCC--RFVL-MFSeas10-MEDATL-b20250531_an-sv11.00.nc",
    },
    # "cmems_mod_med_phy-cur_anfc_4.2km_PT15M-i_202511": {
    #     "freq": "PT15M",  # 15-minute - one file per day
    #     "pattern": "{year}/{month:02d}/{date}_qm-CMCC--RFVL-MFSeas10-MEDATL-b20250531_an-sv11.00.nc"
    # },
    "cmems_mod_med_phy-cur_anfc_detided-4.2km_P1D-m_202511": {
        "freq": "P1D",
        "pattern": "{year}/{month:02d}/{date}_d-CMCC--HCNT-MFSeas10-MEDATL-b20250531_an-sv11.00.nc",
    },
    "cmems_mod_med_phy-mld_anfc_4.2km-2D_PT1H-m_202511": {
        "freq": "PT1H",
        "pattern": "{year}/{month:02d}/{date}_2dh-CMCC--AMXL-MFSeas10-MEDATL-b20250531_an-sv11.00.nc",
    },
    "cmems_mod_med_phy-mld_anfc_4.2km_P1D-m_202511": {
        "freq": "P1D",
        "pattern": "{year}/{month:02d}/{date}_d-CMCC--AMXL-MFSeas10-MEDATL-b20250531_an-sv11.00.nc",
    },
    "cmems_mod_med_phy-mld_anfc_4.2km_P1M-m_202511": {
        "freq": "P1M",
        "pattern": "{year}/{date}_m-CMCC--AMXL-MFSeas10-MEDATL-b20250531_an-sv11.00.nc",
    },
    "cmems_mod_med_phy-sal_anfc_4.2km-2D_PT1H-m_202511": {
        "freq": "PT1H",
        "pattern": "{year}/{month:02d}/{date}_2dh-CMCC--PSAL-MFSeas10-MEDATL-b20250531_an-sv11.00.nc",
    },
    # "cmems_mod_med_phy-sal_anfc_4.2km-3D_PT1H-m_202511": {
    #     "freq": "PT1H",
    #     "pattern": "{year}/{month:02d}/{date}_3dh-CMCC--PSAL-MFSeas10-MEDATL-b20250531_an-sv11.00.nc"
    # },
    "cmems_mod_med_phy-sal_anfc_4.2km_P1D-m_202511": {
        "freq": "P1D",
        "pattern": "{year}/{month:02d}/{date}_d-CMCC--PSAL-MFSeas10-MEDATL-b20250531_an-sv11.00.nc",
    },
    "cmems_mod_med_phy-sal_anfc_4.2km_P1M-m_202511": {
        "freq": "P1M",
        "pattern": "{year}/{date}_m-CMCC--PSAL-MFSeas10-MEDATL-b20250531_an-sv11.00.nc",
    },
    "cmems_mod_med_phy-ssh_anfc_4.2km-2D_PT1H-m_202511": {
        "freq": "PT1H",
        "pattern": "{year}/{month:02d}/{date}_2dh-CMCC--ASLV-MFSeas10-MEDATL-b20250531_an-sv11.00.nc",
    },
    "cmems_mod_med_phy-ssh_anfc_4.2km_P1D-m_202511": {
        "freq": "P1D",
        "pattern": "{year}/{month:02d}/{date}_d-CMCC--ASLV-MFSeas10-MEDATL-b20250531_an-sv11.00.nc",
    },
    "cmems_mod_med_phy-ssh_anfc_4.2km_P1M-m_202511": {
        "freq": "P1M",
        "pattern": "{year}/{date}_m-CMCC--ASLV-MFSeas10-MEDATL-b20250531_an-sv11.00.nc",
    },
    # "cmems_mod_med_phy-ssh_anfc_4.2km_PT15M-i_202511": {
    #     "freq": "PT15M",
    #     "pattern": "{year}/{month:02d}/{date}_qm-CMCC--ASLV-MFSeas10-MEDATL-b20250531_an-sv11.00.nc"
    # },
    "cmems_mod_med_phy-ssh_anfc_detided-4.2km_P1D-m_202511": {
        "freq": "P1D",
        "pattern": "{year}/{month:02d}/{date}_d-CMCC--SHNT-MFSeas10-MEDATL-b20250531_an-sv11.00.nc",
    },
    "cmems_mod_med_phy-tem_anfc_4.2km-2D_PT1H-m_202511": {
        "freq": "PT1H",
        "pattern": "{year}/{month:02d}/{date}_2dh-CMCC--TEMP-MFSeas10-MEDATL-b20250531_an-sv11.00.nc",
    },
    "cmems_mod_med_phy-cur_anfc_4.2km-2D_PT1H-m_202511": {
        "freq": "PT1H",
        "pattern": "{year}/{month:02d}/{date}_2dh-CMCC--RFVL-MFSeas10-MEDATL-b20250531_an-sv11.00.nc",
    },
    # "cmems_mod_med_phy-tem_anfc_4.2km-3D_PT1H-m_202511": {
    #     "freq": "PT1H",
    #     "pattern": "{year}/{month:02d}/{date}_3dh-CMCC--TEMP-MFSeas10-MEDATL-b20250531_an-sv11.00.nc"
    # },
    "cmems_mod_med_phy-tem_anfc_4.2km_P1D-m_202511": {
        "freq": "P1D",
        "pattern": "{year}/{month:02d}/{date}_d-CMCC--TEMP-MFSeas10-MEDATL-b20250531_an-sv11.00.nc",
    },
    "cmems_mod_med_phy-tem_anfc_4.2km_P1M-m_202511": {
        "freq": "P1M",
        "pattern": "{year}/{date}_m-CMCC--TEMP-MFSeas10-MEDATL-b20250531_an-sv11.00.nc",
    },
    "cmems_mod_med_phy-wcur_anfc_4.2km_P1D-m_202511": {
        "freq": "P1D",
        "pattern": "{year}/{month:02d}/{date}_d-CMCC--LRZA-MFSeas10-MEDATL-b20250531_an-sv11.00.nc",
    },
    "cmems_mod_med_phy-wcur_anfc_4.2km_P1M-m_202511": {
        "freq": "P1M",
        "pattern": "{year}/{date}_m-CMCC--LRZA-MFSeas10-MEDATL-b20250531_an-sv11.00.nc",
    },
}


def generate_filenames(year, month, dataset_config):
    """Generate filenames for a dataset based on frequency."""
    freq = dataset_config["freq"]
    pattern = dataset_config["pattern"]
    filenames = []

    if freq == "P1M":
        # Monthly: only one file for the month (1st day of month)
        date_str = f"{year}{month:02d}01"
        filename = pattern.format(date=date_str, year=year, month=month)
        filenames.append(filename)
    else:
        # Daily or sub-daily: one file per day
        num_days = monthrange(year, month)[1]
        for day in range(1, num_days + 1):
            date_str = f"{year}{month:02d}{day:02d}"
            filename = pattern.format(date=date_str, year=year, month=month)
            filenames.append(filename)

    return filenames


def generate_xml(year, month, output_file=None):
    """Generate the complete XML for a given month."""
    # Current timestamp for the delivery date
    now = datetime.datetime.now(datetime.timezone.utc)
    delivery_date = now.strftime("%Y%m%dT%H%M%SZ")

    xml_lines = [
        '<?xml version="1.0" ?>',
        f'<delivery product="MEDSEA_ANALYSISFORECAST_PHY_006_013" PushingEntity="MED-CMCC-LECCE-IT" date="{delivery_date}">',
        "",
    ]

    # Generate datasets
    for dataset_name, dataset_config in DATASETS.items():
        xml_lines.append(f'    <dataset DatasetName="{dataset_name}">')

        filenames = generate_filenames(year, month, dataset_config)

        for filename in filenames:
            xml_lines.append(
                f'        <file FileName="{filename}" StartUploadTime="" StopUploadTime="" Checksum="" FileType="" FinalStatus="">'
            )
            xml_lines.append("                <KeyWord>Delete</KeyWord>")
            xml_lines.append("")
            xml_lines.append("        </file>")

        xml_lines.append("    </dataset>")
        xml_lines.append("")

    xml_lines.append("</delivery>")

    xml_content = "\n".join(xml_lines)

    if output_file:
        with open(output_file, "w") as f:
            f.write(xml_content)
        print(f"XML file generated: {output_file}")
    else:
        print(xml_content)

    return xml_content


def main():
    if len(sys.argv) < 3:
        print("Usage: python generate_delivery_xml.py YYYY MM [output_file.xml]")
        print("Example: python generate_delivery_xml.py 2023 01 delivery_2023_01.xml")
        sys.exit(1)

    try:
        year = int(sys.argv[1])
        month = int(sys.argv[2])

        if not (1 <= month <= 12):
            print("Error: Month must be between 1 and 12")
            sys.exit(1)

        output_file = sys.argv[3] if len(sys.argv) > 3 else None

        generate_xml(year, month, output_file)

    except ValueError as e:
        print(f"Error: Invalid year or month format. {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
