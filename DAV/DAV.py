from netCDF4 import Dataset
import numpy as np
import matplotlib.pyplot as plt
import cv2 as cv
from mpl_toolkits.axes_grid1 import make_axes_locatable
from scipy import ndimage, misc
import numba
import pandas as pd
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from pyproj import Proj, transform
from geopy.distance import geodesic
import s3fs

from sklearn.metrics import mean_squared_error, mean_absolute_error

from osgeo import gdal, osr
import rasterio

from glob import glob

njit=numba.njit

# Funciones para la realización del DAV MAP

"""
Crea una matriz con los vectores que unen al pixel de referencia con el resto de pixeles (pos)
y crea una matriz con el vector gradiente de cada pixel del area de estudio (grad). Los argumentos
son: 
mx-> matriz de la componente en X del vector gradiente
mx-> matriz de la componente en Y del vector gradiente
"""
@njit
def mtx(mx,my):
    pos=[]
    grad=[]
    for i in range(my.shape[0]):
        for j in range(my.shape[1]):
            pos.append(np.array([float(j),float(-i-1)]))
            grad.append(np.array([mx[i,j],my[i,j]]))
    
    return pos ,grad

"""
Calcula el angulo entre entre todos los vectores de posicion y el vector gradiente correspondientes
a un pixel de referencia. Los angulos se almacenan en una lista y posteriormente se calucla la Varianza.
El valor de la varianza se almacena en una nueva matriz y su posicion es coincidente con la del pixel de
referencia. Esta función genera el DAV. Los argumentos son:
pos-> resultado de la funcion anterior
grad-> resultado de la funcion anterior
c0-> Posición (i,j) del pixel de referencia
"""
@njit
def dav(pos,grad,c0):
    
    p=[i-np.array(c0) for i in pos]

    ang=[]
    
    for i in range(len(grad)):
        if ((p[i][0]==0.0 and p[i][1]==0.0) or (grad[i][0]==0.0 and grad[i][1]==0.0)):
            pass
        else:
            ang.append(np.degrees(np.arccos((np.dot(grad[i],p[i])/((np.hypot(grad[i][0],grad[i][1]))*(np.hypot(p[i][0],p[i][1])))))))
        
    ang=np.nanvar(np.array(ang))

    return ang

"""
Itera sobre cada pixel estableciendo una region de un radio, en km, determinado. Una vez que se 
selecciona el pixel central, se hace un subarreglo con la region correspondiente y se calcula el DAV
de dicho pixel. Los argumento son:
kx-> matriz de la componente en X del vector gradiente
ky-> matriz de la componente en Y del vector gradiente
r-> radio, en km, que definirá la region de estudio para cada pixel. En los articulos se sugiere 
utilizar un radio de 350km, aunque en la práctica he notado que si se usa 400 o 450km la estimación
aprenta ser más robusta para tormentas de gran área.

Esta función regresa la matriz correspondiente al DAV MAP de la imagen estudiada
"""
@njit
def davM(kx,ky,r):
    
    dv=[]
    
    for i in range(kx.shape[0]):
        for j in range(kx.shape[1]):
            if (i<r):
                if (j<r):
                    hx=kx[:i+r+1,:j+r+1]
                    hy=ky[:i+r+1,:j+r+1]
                    p=kx[i,j]
                else:
                    hx=kx[:i+r+1,j-r:j+r+1]
                    hy=ky[:i+r+1,j-r:j+r+1]
                    p=kx[i,j]
            else:
                if (j<r):
                    hx=kx[i-r:i+r+1,:j+r+1]
                    hy=ky[i-r:i+r+1,:j+r+1]
                    p=kx[i,j]
                else:
                    hx=kx[i-r:i+r+1,j-r:j+r+1]
                    hy=ky[i-r:i+r+1,j-r:j+r+1]
                    p=kx[i,j]

            b=mtx(hx,hy)
            
            bg=b[1]
            bp=b[0]
            c0=(np.where(hx==p)[0][0],-1-np.where(hx==p)[1][0])

            d=dav(bp,bg,c0)
            
            dv.append(d)
            
    dv=np.array(dv).reshape(kx.shape)
    
    return dv

"""
Función para abrir un .nc correspondiente a una imagen goes, reproyectarla epsg=4326, convertir
la imagen a una matriz y recortarla a una region especifica. Los argumentos son:
rr->ruta de la imagen
cl->region de corte de la imagen (xmin,xmax,ymin,ymax)
"""
def prDV(rr,cl):
    img=gdal.Open(rr)
    sub=gdal.Open(img.GetSubDatasets()[0][0])
    
    gdal.Warp('output_raster.tif',sub,dstSRS='EPSG:4326')
    
    abr=gdal.Open('output_raster.tif')
    
    data3=np.array(abr.ReadAsArray())
    data3=np.where(data3 == -1,np.nan,data3)
    
    coli = round((cl[0] - gt[0]) / gt[1]) 
    colf = round((cl[1] - gt[0]) / gt[1]) 
    rowi = round((cl[2] - gt[3]) / gt[5])
    rowf = round((cl[3] - gt[3]) / gt[5])
    
    dc=data3[rowf:rowi+1,coli:colf+1]
    
    return abr,dc

"""
Esta función calcula los gradientes necesarios para calcular el DAV MAP, además redimensiona la imagen
para acelerar el proceso. Finalmente, filtra la imagen segun un umbral para el DAV (en los articulos se
propone 1250 a 1700) y calcula las posiciones del centro de cada pixel, de esta forma se determina la
lat y lon del sitio que podria ser el centro de la tormenta por tener un valor minimo de DAV. Los argumentos son:
im->imagen abierta con gdal
arr->arreglo correspondiente a la imagen cortada a una region especifica
r->radio para realizar el DAV en km
d-> que tanto se va a reducir en proporcion la imagen. Si d=2 entonces la imagen se reduce a la mitad de 
su tamaño original. Para imagenes del GOES 16 se reduce a 5 veces su tamaño orignal (d=5) y no hay cambio
aparente en la calidad del resultado pero si en el tiempo
um->umbral de filtrado para el DAV
cl->region de corte de la imagen (xmin,xmax,ymin,ymax)
"""
def ttd(im,arr,r,d,um,cl):
    ggt=im.GetGeoTransform()
    ori = (0, 0)
    cuad = (-1*ggt[-1], ggt[1])
    res=round(geodesic(ori, cuad).km*1000,3)
    dim=arr.shape
    dt=cv.resize(arr, dsize=(round(dim[1]/d),round(dim[0]/d)),interpolation=cv.INTER_CUBIC)
    res=d*res
    sx = ndimage.sobel(dt, axis=0, mode='constant')
    sy = ndimage.sobel(dt, axis=1, mode='constant')
    rd=round(r*1000/res)
    print('Calculando DAV MAP...')
    g=davM(sx.astype(float),sy.astype(float),rd)
    dim=g.shape
    print('Calculando Posiciones...')
    loc=np.where((um[0]<g) & (g<um[1]))
    lon=(cl[1]-(dim[1]-loc[1])*ggt[1]*d)+(ggt[1]*d)/2
    lat=(cl[-1]+loc[0]*ggt[-1]*d)-(ggt[1]*d)/2
    return g ,[lat,lon],g[loc]

