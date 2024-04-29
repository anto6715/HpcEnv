#!/usr/bin/env python

import netCDF4 as ncdf
import numpy as np
import os

dimensionVar = ['time_counter', 'nav_lon', 'nav_lat', 'deptht', 'tbnds', 'time_counter_bnds', 'time_counter_bounds']
timeVar = ['time_counter', 'time_counter_bnds', 'time_counter_bounds']


def get_args():
    import argparse

    parse = argparse.ArgumentParser(description="Compute daily mean file from hourly mean file")

    # General args
    parse.add_argument('inputFile', type=str, help="Path of file")
    return parse.parse_args()


def main():
    args = get_args()
    inputFile = args.inputFile
    outFile = os.path.basename(inputFile).replace('1h', '1d')

    hourlyFile = ncdf.Dataset(inputFile, 'r')
    dailyFile = ncdf.Dataset(outFile, 'w')

    # copy dimensional variables
    for name, dimension in hourlyFile.dimensions.items():
        dailyFile.createDimension(
            name, (len(dimension) if not dimension.isunlimited() else None))

    # create all necessary variables in dailyFile
    for name, variable in hourlyFile.variables.items():
        dailyFile.createVariable(name, variable.datatype, variable.dimensions)
        # copy variable attributes all at once via dictionary
        dailyFile[name].setncatts(hourlyFile[name].__dict__)

    ncVars = hourlyFile.variables
    for ncVar in ncVars:
        if ncVar not in dimensionVar:
            print('Compute mean of: ', ncVar)
            hVars = ncVars[ncVar][:]
            #missing_value = ncVars[ncVar].missing_value
            #hVars[hVars == missing_value] = np.ma.masked
            hourlyVars = 0
            # compute mean of 24 hourly variables to obtain the a daily mean
            for hVar in hVars:
                hourlyVars += hVar
            dailyFile[ncVar][0] = hourlyVars / 24.0
        elif ncVar not in timeVar:
            print('Copy dimension: ', ncVar)
            # var that can be copied as is
            dailyFile[ncVar][:] = hourlyFile[ncVar][:]
        else:
            if ncVar == 'time_counter':
                print('Compute mean of: ', ncVar)
                hourlyTimes = hourlyFile.variables[ncVar][:]
                dailyTime = 0
                for time in hourlyTimes:
                    dailyTime += time
                dailyTime /= len(hourlyTimes)
                dailyFile[ncVar][0] = str(dailyTime)
            else:
                print("Set ", ncVar)
                bndsTimes = hourlyFile.variables[ncVar][:]
                bndsTimes = [bndsTimes[0][0], bndsTimes[-1][1]]
                dailyFile[ncVar][0] = bndsTimes

    hourlyFile.close()
    dailyFile.close()


if __name__ == '__main__':
    main()