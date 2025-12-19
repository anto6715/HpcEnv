#!/usr/bin/env python

import warnings
warnings.filterwarnings("ignore")

import sys
import numpy
import os
import netCDF4



################################################
# FOLDER PATH AND NAME DEFINITIONS
################################################

FileName1=sys.argv[1]
FileName2=sys.argv[2]
FieldName1=sys.argv[3]
FieldName2=sys.argv[4]

try:
	Field1=numpy.ma.asarray(netCDF4.Dataset(FileName1).variables[FieldName1][...])
except Exception as e:
	print(f"FAIL Can't extract {FieldName1} from {FileName1}")

try:
	Field2=numpy.ma.asarray(netCDF4.Dataset(FileName2).variables[FieldName2][...])
except Exception as e:
	print(f"FAIL Can't extract {FieldName2} from {FileName2}")

result='OK'

rmin=(Field1-Field2).min()
if not (rmin == 0) : result='FAIL'

rmax=(Field1-Field2).max()
if not (rmax == 0) : result='FAIL'

rmask=numpy.array_equal(Field1.mask,Field2.mask)
if not rmask: result='FAIL'

print (result,rmin,rmax,rmask,FileName1,FieldName1,FileName2,FieldName2)
