#!/usr/bin/env python

import xarray as xr

VAR_NAMES = ["hfls", "hfss", "rlds", "rsntds", "hfds"]
INPUT_FILES = ("/work/cmcc/am09320/EIS_202411/cmems_rea24/work/CMEMS_flxs_d/out/*_d-CMCC--MFLX-MFSe3r1-MED"
               "-b20240607_re-sv01.00.nc")


def main():
    ds = xr.open_mfdataset(INPUT_FILES)

    for v in VAR_NAMES:
        print(f"Computing min for {v}")
        min_v = ds[v].min().compute()

        print(f"Computing min for {v}")
        max_v = ds[v].max().compute()

        print(f"Min: {min_v}, Max: {max_v}")
        print("\n\n")


if __name__ == "__main__":
    main()
