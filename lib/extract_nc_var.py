#!/usr/bin/env python

import netCDF4 as ncdf

dimensionVar = ['time_counter', 'nav_lon', 'nav_lat', 'deptht', 'tbnds', 'time_counter_bnds', 'lon', 'lat', 'depth'
                'longitude', 'latitude']
timeVar = ['time_counter', 'time_counter_bnds', 'time']


def get_args():
    import argparse

    parse = argparse.ArgumentParser(description="Compute daily mean file from hourly mean file")

    # General args
    parse.add_argument('inputFile', type=str, help="Path of file")
    parse.add_argument('-l', '--list', nargs='+', dest="vars_to_extract", help='List of variable to extract"', required=True)
    # Use like:
    # python arg.py -l 1234 2345 3456 4567
    return parse.parse_args()


def main():
    args = get_args()
    var_to_extract_list = args.vars_to_extract
    inputFile = args.inputFile
    outFile = inputFile.replace('.nc', '_extract.nc')


    completeFile = ncdf.Dataset(inputFile, 'r')
    extractFile = ncdf.Dataset(outFile, 'w')

    # copy dimensional variables
    for name, dimension in completeFile.dimensions.items():
        extractFile.createDimension(
            name, (len(dimension) if not dimension.isunlimited() else None))

    # create all necessary variables in dailyFile
    for name, variable in completeFile.variables.items():
        if name in timeVar or name in dimensionVar or name in var_to_extract_list:
            extractFile.createVariable(name, variable.datatype, variable.dimensions)
            # copy variable attributes all at once via dictionary
            extractFile[name].setncatts(completeFile[name].__dict__)
        else:
            pass

    ncVars = completeFile.variables
    for ncVar in ncVars:
        if ncVar in timeVar or ncVar in dimensionVar or ncVar in var_to_extract_list:
            print('Copy dimension: ', ncVar)
            # var that can be copied as is
            extractFile[ncVar][:] = completeFile[ncVar][:]

    completeFile.close()
    extractFile.close()


if __name__ == '__main__':
    main()
