#!/usr/bin/env python
# coding: utf-8

import xarray as xr
import numpy as np

import os, stat, sys
from os.path import join
from operator import itemgetter

from glob import glob
from datetime import datetime
from pyresample import image, geometry

from config_goes.MainConfig import get_config
from config_goes.params import *



def makeframe(area1, tt):
    lon, lat = area1.get_lonlats()
    lon = lon[0,:]
    lat = lat[:,0]

    outframe = xr.Dataset(coords={'lon': ('lon' , lon),                             
                                  'lat': ('lat', lat), 
                                  'time': ('time', tt)})

    # Basic Attributes for the new NETCDF
    outframe.time.attrs['axis'] = "time"
    outframe.lon.attrs['units'] = "degree"
    outframe.lon.attrs['axis'] = 'lon'
    outframe.lat.attrs['units'] = "degree"
    outframe.lat.attrs['axis'] = 'lat'
    return outframe

def gvar2bt(data, nband):
    # Convertion constants
    c1 = 1.191066e-5
    c2 = 1.438833
    vardic = {'3' : {'m' : 38.8383,
                     'b1' : 29.1287, 
                     'n' : 1522.52, 
                     'a' : -3.625663, 
                     'b2' : 1.010018},
              '4' : {'m' : 5.2285,
                     'b1' : 15.6854, 
                     'n' : 937.23, 
                     'a' : -0.386043, 
                     'b2' : 1.001298},
              '6' : {'m' : 5.5297,
                     'b1' : 16.5892, 
                     'n' : 751.93, 
                     'a' : -0.134688, 
                     'b2' : 1.000481}}
    m, b1, n, a, b2 = itemgetter('m', 'b1', 'n', 'a', 'b2')(vardic[nband])
    # Converting data to BT
    b10 = 1023
    b15 = 32768

    aux = b10 / b15
    bux = b10 - aux * b15
    data = (aux * data + bux)
    data = (data - b1)/m

    data = (c2 * n) / np.log(1 + (c1 * n**3) / data)

    data = (a + (b2 * data)) - 273.15
    # Check max and min value
    # print(np.nanmin(data), np.nanmax(data))
    return data
    

def str2time(ncfile):
    datetime_str = str(ncfile.imageDate.data)+str(ncfile.imageTime.data)
    date = datetime.strptime(datetime_str,'%Y%j%H%M%S')
    return date

def goes13_4k():
    # Dominio 1 remuestreado a aprox 1'
    area_id = 'emcwf'
    description = "4km_resolution"
    proj_id = 'emcwf'
    projection = 'EPSG:4326'
    width = int(2694/2)
    height = int(1906/2)
    area_extent = (-123.3613, 4.1260, -74.8779, 38.4260)
    areas = geometry.AreaDefinition(area_id = area_id, 
                                    description = description, 
                                    proj_id = proj_id, 
                                    projection = projection, 
                                    width = width, height = height, 
                                    area_extent = area_extent)
    return areas
area1 = goes13_4k()

if __name__ == "__main__":
    config = get_config()
    nband = config[GOES.band]
    fpath = config[GOES.input_folder]
    spath = config[GOES.output_folder]

    var0 = 'C0{}'.format(nband)

    oname = 'goes13_2012_C0{}.nc'.format(nband)
    fname = 'goes13*0{}.nc'.format(nband)

    file_b = sorted(glob(join(fpath,fname)))
    nfiles = len(file_b)

    if nfiles == 0:
        print('No files found in path!')
        sys.exit()

    encodedic = {}
    encodedic[var0] = {'_FillValue': -274,
                       'zlib': True,
                       'complevel' : 9}
    encodedic['time'] = {'units':'seconds since 2000-01-01 12:00:00', 'calendar':'gregorian'}

    # Organizing data
    for file in range(nfiles):
        frame = xr.open_dataset(file_b[file])
        if file == 0:
            data = frame.data.data.reshape(1246, 3464)
            tt = np.array([str2time(frame)])
            slat = frame.lat.data
            slon = frame.lon.data
        else:
            aux = frame.data.data.reshape(1246, 3464)
            tt = np.concatenate((tt, np.array([str2time(frame)])))
            data = np.stack([data, aux], axis=2)

    data = gvar2bt(data, nband)
    outframe = makeframe(area1, tt)

    swath = geometry.SwathDefinition(lons=slon, lats=slat)
    containr = image.ImageContainerNearest(data,
                                           swath,
                                           radius_of_influence=5000,
                                           nprocs=6).resample(area1).image_data


    outframe[var0] = (['lat', 'lon', 'time'], containr)
    outframe[var0].attrs['axis'] = "lat lon time"
    outframe[var0].attrs['resample_method'] = "Nearest_Neighbour"
    outframe.to_netcdf(path=spath+oname,
                       format='netCDF4',
                       encoding=encodedic,
                       unlimited_dims=['time'])

    print('DONE')





