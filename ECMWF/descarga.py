#!/usr/bin/env python
from ecmwfapi import ECMWFDataServer

#server = ECMWFDataServer()
server = ECMWFDataServer(url="https://api.ecmwf.int/v1",key="faca731681d7635f4ae68b8c45dcaebc",email="tai@atmosfera.unam.mx")
#or
#server = ECMWFService("mars", url="https://api.ecmwf.int/v1",key="faca731681d7635f4ae68b8c45d

server.retrieve({
    'stream'    : "oper",
    'step'	: "0",

#    'levtype'   : "sfc",
#    'param'	: "134.128/151.128/165.128/166.128/167.128",


    'levtype'   : "pl",
    'levelist'	: "1/2/3/5/7/10/20/30/50/70/100/125/150/175/200/225/250/300/350/400/450/500/550/600/650/700/750/775/800/825/850/875/900/925/950/975/1000",
    'param'     : "60.128/129.128/130.128/131.128/132.128/135.128/138.128/155.128",

    'dataset'   : "interim",
    'step'      : "0",
    'grid'      : "0.75/0.75",
    'time'      : "00/06/12/18",
    'date'      : "2012-08-01/to/2012-08-10",
    'type'      : "an",
    'class'     : "ei",
    'area'      : "0/-120/50/-50",
    'format'    : "netcdf",
#    'target'    : "2012-08-01_2012-08-10_00061218_sfc.nc"
    'target'    : "2012-08-01_2012-08-10_00061218_pres.nc"
})
