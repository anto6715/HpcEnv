#!/usr/bin/env python

import sys
import xarray as xr
import numpy as np


def main():
    input_file = sys.argv[1]
    var_name = sys.argv[2]

    dt = xr.open_dataset(input_file)
    var_dt = dt[var_name]

    np_array = np.nan_to_num(var_dt)

    print(f"Contains all nan: {np.isnan(np_array)}")
    print(f"Max: {np_array.max()}")
    print(f"Min: {np_array.min()}")


if __name__ == '__main__':
    main()
