#! /usr/bin/env python

import json
import warnings
import lib.netcdf as nclib

warnings.filterwarnings("ignore")


# mpl.use('Agg')


def main(raw_args=None):
    args = get_args(raw_args)

    # General args
    inputFile = args.inputFile  # first file path
    var = args.var  # Var to be plotted
    title = args.title
    tDescr = args.tDescr  # Bulletin day
    outFileName = args.outFileName
    input_files = args.inputFiles
    inputFile2 = args.inputFile2  # second file path (if is not None then diff src is called)
    # Map only
    depthLevel = args.depthLevel  # Depth level to be plotted
    lonLat = json.loads(args.lonLat)
    grid = args.grid
    mapLevels = args.mapLevels
    clbLim = args.clbLim
    cmap = args.cmap
    # Timeseries only
    mix = args.mix
    legend = args.legend
    freq = args.freq
    xTicks = args.xTicks
    lr = args.linearRegression
    yLim = args.yLim
    # Diff src
    diff = args.diff  # difference flag
    diffMask = args.diffMask  # difference flag
    diffForce = args.diffForce  # difference flag
    findMaxDiff = args.findMaxDiff
    # Map Currents
    curr = args.curr  # current flag
    qd = args.qd
    qScale = args.qScale
    qWidth = args.qWidth
    var2 = args.var2  # Second current component
    map = args.map
    ts = args.ts
    # Climatology
    clim = args.clim  # climatology flag

    if legend is not None:
        legend = json.loads(args.legend)

    if not map and not ts:
        ts, map = nclib.get_plot_type(inputFile)

    # ****************************** MAP PLOT ****************************** #
    if map:
        print("Starting map src...")
        if curr:
            from src.map.interfaces import currents
            currents.currents_plot(inputFile, inputFile2, var, var2, depthLevel, title,
                                   tDescr, lonLat, outFileName, mapLevels, qd, grid, qScale, qWidth, clbLim)
        elif diff:
            from src.map.interfaces import diff
            diff.diff_plot(inputFile, inputFile2, var, depthLevel, title, tDescr, lonLat, outFileName, mapLevels,
                           diffMask, diffForce, clbLim, findMaxDiff)
        else:
            from src.map.interfaces import standard
            standard.standard_plot(inputFile, var, depthLevel, title, tDescr, lonLat, outFileName, mapLevels, clbLim,
                                   cmap)
    # ****************************** TIMESERIES PLOT ****************************** #
    elif ts:
        print("Starting timeseries src...")
        if diff:
            from src.timeseries.interfaces import diff
            diff.diff_plot(inputFile, inputFile2, var, title, tDescr, xTicks, outFileName, freq, yLim=yLim)
        elif clim:
            from src.timeseries.interfaces import climatology
            climatology.climatology_plot(inputFile, var, title, tDescr, xTicks, outFileName, yLim=yLim)
        elif mix:
            from src.timeseries.interfaces import mixed
            mixed.mix_plot(inputFile, var, title, tDescr, xTicks, outFileName, freq, input_files=input_files,
                           yLim=yLim, legend=legend)
        else:
            from src.timeseries.interfaces import standard
            standard.standard_plot(inputFile, var, title, tDescr, xTicks, outFileName, freq,
                                   lr=lr, yLim=yLim, legend=legend)
    else:
        raise Exception('Please select a src mode using --map or --ts')


def get_args(raw_args=None):
    import argparse

    parse = argparse.ArgumentParser(description="Map - Timeseries plotting tool")

    # General args
    parse.add_argument('inputFile', type=str, help="Path of file")
    parse.add_argument('var', type=str, help="Variable to src")
    parse.add_argument('--title', type=str, default=None, help="Title")
    parse.add_argument('--tDescr', type=str, default=None, help="Title description")
    parse.add_argument('--o', dest="outFileName", type=str, default=None, help="Outfile name")
    parse.add_argument('--list', dest="inputFiles", nargs='+', type=str, default=list(), help="Output directory")
    parse.add_argument('--i2', dest='inputFile2', type=str, default=None, help="Path of second input file")
    # Map only
    parse.add_argument('--depthLevel', type=int, default=0, help="Depth level, surface by default")
    parse.add_argument('--lonLat', type=str, default="[-18.125, 36.3, 30, 46]", help='Map coordinates')
    parse.add_argument('--grid', type=int, default=None, help='Map grid size')
    parse.add_argument('--mapLevels', type=int, default=500, help='How many colors represent in the map')
    parse.add_argument('--clbLim', type=str, default=None, help='Set statically the color bar limits')
    parse.add_argument('--cmap', type=str, default=None, help='Set color map')
    # Timeseries only
    parse.add_argument('--mix', action='store_true', help='Enable mixed plot')
    parse.add_argument('--legend', dest='legend', type=str, default=None, help='Timeseries legend')
    parse.add_argument('--freq', dest='freq', type=str, default=None, help='NetCDF4 data frequency')
    parse.add_argument('--yLim', dest='yLim', type=str, default=None, help='Y-axis limits')
    parse.add_argument('--xTicks', dest='xTicks', type=int, default=20,
                       help="Ticks number on x axis")
    parse.add_argument('--lr', dest='linearRegression', action='store_true', help="Enable Linear Regression")
    # Diff src
    parse.add_argument('--diff', action='store_true', help="Enable difference map mode")
    parse.add_argument('--diffMask', action='store_true', help="Enable mask-difference map mode")
    parse.add_argument('--diffForce', action='store_true',
                       help="Try this command if some differences are not shown in the map")
    parse.add_argument('--findMaxDiff', action='store_true', help="Find automatically the level and the coordinate"
                                                                  "with the max difference and plot it")

    # Map Currents
    parse.add_argument('--curr', action='store_true', help="Enable currents map mode")
    parse.add_argument('--qd', dest='qd', type=int, default=12, help='Quiver density')
    parse.add_argument('--qScale', dest='qScale', type=float, default=15,
                       help='Quiver scale, the lower the value the greater the quiver length')
    parse.add_argument('--qWidth', dest='qWidth', type=float, default=0.0012, help='Quiver width')
    parse.add_argument('--var2', type=str, help="Second variable in current map")
    # Plot type
    parse.add_argument('--map', action='store_true', help="Enable map src mode")
    parse.add_argument('--ts', action='store_true', help="Enable timeseries src mode")
    # Climatology
    parse.add_argument('--clim', action='store_true', help="Enable climatology src mode")
    parse.add_argument('--timeRange', dest='timeRange', type=str, default=None,
                       help="Climatology timeseries time range")
    parse.add_argument('--climatology', action='store_true', help="Enable climatology timeseries mode")

    args = parse.parse_args(raw_args)
    print(args)
    return args


if __name__ == '__main__':
    main()
