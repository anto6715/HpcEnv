#!/usr/bin/env python

"""
Set correct analysis bulletin day in according to file date. Force all file to have analysis attribute


Jul 2024
Antonio Mariani
"""

import argparse
import logging
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

from netCDF4 import Dataset

########################
# LOGGING
########################
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] - %(levelname)s: %(message)s",
    # format='[%(asctime)s] - %(levelname)s - %(name)s.%(funcName)s: %(message)s',
    handlers=[
        # logging.FileHandler('example.log')    # to create a log files
        logging.StreamHandler()
    ],
)
logger = logging.getLogger(__name__)

########################
# VARIABLES
########################
BULLETIN = re.compile(r"b\d{8}")


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_dir", type=Path, help="Input file")

    return parser.parse_args()


def get_next_two_week_tuesday(input_date: datetime) -> datetime:
    weekday = input_date.weekday()
    if weekday == 0:
        tuesday = input_date + timedelta(days=1)
    elif weekday == 1:
        tuesday = input_date
    else:
        tuesday = input_date - timedelta(days=weekday - 1)

    return tuesday + timedelta(days=14)


def main():
    args = get_args()
    input_dir: Path = args.input_dir
    input_dir = input_dir.resolve()

    for f in input_dir.iterdir():
        if not f.as_posix().endswith(".nc"):
            logger.warning(f"Skipping {f}")
            continue
        logger.info("Processing %s", f)
        output_filename = f.as_posix()
        ########################
        # FIX BULLETIN DATE
        ########################

        # file date
        fdate_yyyymmdd = f.name[:8]
        fdate = datetime(
            year=int(fdate_yyyymmdd[:4]),
            month=int(fdate_yyyymmdd[4:6]),
            day=int(fdate_yyyymmdd[6:8]),
        )

        # bulletin dates
        bdate_yyyymmdd = BULLETIN.search(f.name).group()[1:]
        correct_bdate = get_next_two_week_tuesday(fdate)
        correct_bdate_yyyymmdd = correct_bdate.strftime("%Y%m%d")

        # generate final filename
        if bdate_yyyymmdd != correct_bdate_yyyymmdd:
            logger.debug(f"Old bulletin: {bdate_yyyymmdd}")
            logger.debug(f"Correct bulletin: {correct_bdate_yyyymmdd}")

            logger.info(f"Renaming b{bdate_yyyymmdd} to b{correct_bdate_yyyymmdd}")
            output_filename = output_filename.replace(
                f"b{bdate_yyyymmdd}", f"b{correct_bdate_yyyymmdd}"
            )

        ########################
        # RENAME SM/FC to AN
        ########################
        found_fc = found_sm = False
        if "fc" in f.name:
            logger.info("Renaming fc to an")
            output_filename = output_filename.replace("fc", "an")
            found_fc = True
        elif "sm" in f.name:
            logger.info("Renaming sm to an")
            output_filename = output_filename.replace("sm", "an")
            found_sm = True

        # rename file
        if f.as_posix() != output_filename:
            logger.info(f"Renaming {f.as_posix()} to {output_filename}")
            os.rename(f.as_posix(), output_filename)

        ########################
        # UPDATE NETCDF ATTRS
        ########################
        with Dataset(output_filename, "a") as ncfile:
            # bulletin_date
            logger.info(f"Patching bulletin_date to {correct_bdate_yyyymmdd}")
            ncfile.setncattr("bulletin_date", correct_bdate_yyyymmdd)

            if found_sm or found_fc:
                # bulletin_type
                bulletin_type = "analysis"
                logger.info(f"Patching bulletin_type to {bulletin_type}")
                ncfile.setncattr("bulletin_type", bulletin_type)

        print("\n", file=sys.stderr)


if __name__ == "__main__":
    main()
