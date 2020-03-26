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

## Las siguientes funciones han sido ajustadas para trabajar con los netCDF de Jorge

"""
prDV abre el netCDF, lo corta de tal forma que la imagen cubra un area rectangular, apartir de los
datos del CDF se obtiene el vector de geotransformacion y la resolucion de cada pixel. Parametros:

rr->ruta de la imagen
"""
def prDV(rr):
    
    ruta=rr
    fh = Dataset(ruta, mode='r')

    lons = np.array(fh.variables['lon'][:])
    lats = np.array(fh.variables['lat'][:])
    time = fh.variables['time'][:]
    c06 = np.array(fh.variables['C06'][:,:,0])

    c06=np.where(c06 == 0,np.nan,c06)

    c06aj=c06[:,400:]
    lonsaj=lons[400:]

    ggt=(lonsaj.min(),lonsaj[1]-lonsaj[0],0,lats.max(),0,lats[1]-lats[0])

    ori=[lats[0],lonsaj[0]]
    cuad=[lats[1],lonsaj[1]]

    res=round(geodesic(ori, cuad).km*1000,3)
    
    return c06aj,ggt,res

"""
Esta funcion calcula el DAVmap y las posiciones de los valores DAV que cumplan un cierto umbral. Parametros:
ggt-> Vector de GeoTransformacion con la estructura de GDAL
res-> resolucion de la imagen en metros
arr-> matriz extraida del netcdf y previamente cortada por la funcion prDV
r-> radio de la region que se en la que se calculara el DAV para cada pixel
d-> factor por el cual se va redimensionar la matriz, si d=2 la matriz se reducira a la mitad de su tamaño original, esta reduccion sirve
para reducir el tiempo de calculo
um-> lista que define el intervalo del umbral 
"""    
def ttd(ggt,res,arr,r,d,um):
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
    lon=(ggt[0]+(loc[1])*ggt[1]*d)+(ggt[1]*d)/2
    lat=(ggt[-3]+loc[0]*ggt[-1]*d)-(ggt[1]*d)/2

    return g ,[lat,lon],g[loc],dt

"""
La función tor, va a filtrar los datos en un dataframe dado, la idea es que pueda identificar un unico dato (correspondiente al centro) de cada
tormenta. Parametros:
rad-> Radio en km a considerar por cada tormenta
rs-> DataFrame ordenado segun el valor del DAV, que contenga un identiifcador unico (FECHA) y las coordenadas en latitud y longitud
"""    
def tor(rad,rs):
    
    df=pd.DataFrame()

    for i in set(rs.Fecha):

        rf=rs[rs.Fecha==i].reset_index(drop=True).sort_values(by='DAV')
        k=0
        ind=0
        l=0
        #print(i)

        while k!=len(rf)-1:

            k=ind
            mk=[]
            ori=(rf.loc[k].Lat,rf.loc[k].Lon)

            #print(k)

            for j in rf.index[l:]:

                cuad=(rf.loc[j].Lat,rf.loc[j].Lon)
                dis=geodesic(ori, cuad).km

                if dis>rad:
                    mk.append(True)
                else:
                    mk.append(False)   

            mk[0]=True          
            rf=rf.loc[k:,:][mk].sort_values(by='DAV')

            #print(rf.index)

            l=1

            df=df.append(rf.loc[k])

            if len(rf.index)>1:
                ind=rf.index[1]
            else:
                k=len(rf)-1
            
    return df.reset_index(drop=True).sort_values(by=['Fecha','DAV'])


"""
La funcion mz() va a integrar todas las funciones anteriores. Esta funcion aun no esta diseñada para iterar sobre un grupo de imagenes.
Además, mz va a exportar un tif correspondiente al DAVmap, un csv con los datos de la imagen (DAVs minimos tentativos a ser el centro de las tormentas,
nombre de la imagen, latitud, longitud, columna y renglon del pixel). Parametros:

rr->Ruta
d-> factor por el cual se va redimensionar la matriz, si d=2 la matriz se reducira a la mitad de su tamaño original, esta reduccion sirve
para reducir el tiempo de calculo
rad-> radio de la region que se en la que se calculara el DAV para cada pixel
um-> lista que define el intervalo del umbral 
rt-> Radio en km a considerar por cada tormenta
"""
def mz(rr,d,rad,um,rt):


    va=prDV(rr)
        
    db=ttd(va[1],va[2],va[0],rad,d,um)
    
    df=pd.DataFrame({"Fecha":rr[-18:],"DAV":db[-2],"Lat":db[1][0],"Lon":db[1][1]})
    
    df=df.sort_values(by='DAV')
    
    dff=tor(rt,df)
    dff.rename(columns={"Fecha": "Imagen"},inplace=True)
    
    dst_ds = gdal.GetDriverByName('GTiff').Create(rr[-18:-3]+'DAV.tif', db[0].shape[1],  db[0].shape[0], 1, gdal.GDT_CFloat32)
    dst_ds.SetGeoTransform([va[1][0],va[1][1]*d,va[1][2],va[1][3],va[1][4],va[1][5]*d])   
    srs = osr.SpatialReference()           
    srs.ImportFromProj4("+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs ") 
    dst_ds.SetProjection(srs.ExportToWkt()) 
    dst_ds.GetRasterBand(1).WriteArray(db[0])   
    dst_ds.FlushCache()                    

    dst_ds = None
 
    row=round((dff.Lat-va[1][-3])/(va[1][5]*d))
    col=round((dff.Lon-va[1][0])/(va[1][1]*d))
    
    dff['Col']=col
    dff['Row']=row
    
    dff.to_csv('DAV.csv')
    
    plt.imshow(db[-1],cmap='Greys')
    plt.scatter(col,row,c='r',s=15)
    plt.show();
    
    print("Proceso Terminado")
    
    return db[0],dff    

## Prueba del procedimiento

AI=mz("C:/Users/thewo/Desktop/quinto/icat/IMG/goes13_2012_C06.nc",5,500,[1250,1950],300)  
