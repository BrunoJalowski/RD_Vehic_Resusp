#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar 21 11:34:11 2025

@author: brunojalowski

DATASET SOURCE: https://brasil.mapbiomas.org/metodo-mapbiomas-solo/


"""
import os
import rasterio
import rioxarray as rxr
import glob
from pathlib import Path
import matplotlib.pyplot as plt
from road_preprocess import gdf
import xarray as xr
from rasterio.enums import Resampling
import numpy as np
import geopandas as gpd
from rasterio.features import shapes

#%% PATH
project_path = Path('/home/brunojalowski/Documentos/RD_Vehic_Resusp/dados_entrada')
silt_fraction_path = project_path /'Silt_Fraction'


#%% Opening file
files = glob.glob(str(silt_fraction_path / '*.tif'))

#%%
silt_fraction = rxr.open_rasterio(silt_fraction_path / 'mapbiomas-brazil-collection2-beta-000_010cm-granulometry_silt_percent-0000095232-0000063488.tif', band_as_variable=True)

#%%Defining CRS
silt_fraction.rio.write_crs("epsg:4326", inplace=True)

#%% Downscaling

# Reduzindo a dimensão do raster 1/10
downscale_factor = 1/10
    
# nova largura e altura
new_width = silt_fraction.rio.width * downscale_factor
new_height = silt_fraction.rio.height * downscale_factor
    
# faz o downscaling
silt_fraction = silt_fraction.rio.reproject(silt_fraction.rio.crs, shape=(int(new_height),
                                                     int(new_width)),
                              resampling=Resampling.bilinear)

#%%Plotando os dois para ver se encaixam
"""
fig, ax = plt.subplots()
xr.plot.pcolormesh(darray=silt_fraction['band_1'][:,:],ax=ax)
gdf.plot(ax=ax, color="r")

minx, miny, maxx, maxy = gdf.total_bounds
ax.set_xlim(minx-0.01, maxx+0.01)
ax.set_ylim(miny-0.01, maxy+0.01)

ax.set_title('Encaixe vias e raster')
ax.set_xlabel('Longitude')
ax.set_ylabel('Latitude')

plt.show()

del minx, miny, maxy, maxx

"""
#%% MÈTODO 1

# Designando valores de teor de silte para cada trecho de via
values = []
for _, row in gdf.iterrows():
    line = row['geometry']  

    if line.geom_type == 'LineString':
        line_values = []  
        """ Para cada ponto na LineString, pega os índices mais próximos e com 
         eles o teor de silte"""
        for point in line.coords:
            lon, lat = point
            lat_idx = np.abs(silt_fraction['y'] - lat).argmin()  
            lon_idx = np.abs(silt_fraction['x'] - lon).argmin()  
            value = silt_fraction['band_1'][lon_idx, lat_idx].values  
            line_values.append(value)
        values.append(line_values)  

    else:
        values.append(None)  


gdf['silt_fraction'] = values
gdf.loc[:,'silt_fraction'] = gdf.loc[:,'silt_fraction'].str[0]

del lat, lat_idx, line, line_values,lon,lon_idx,point,row

#%% Assignment results
"""
fig, ax = plt.subplots(figsize=(10, 10))
xr.plot.pcolormesh(darray=silt_fraction['band_1'],ax=ax, alpha=0.5)
gdf.plot(column='silt_fraction', ax=ax, cmap='viridis')  

minx, miny, maxx, maxy = gdf.total_bounds
ax.set_xlim(minx-0.01, maxx+0.01)
ax.set_ylim(miny-0.01, maxy+0.01)

ax.set_title('Silt Fraction by road')
ax.set_xlabel('Longitude')
ax.set_ylabel('Latitude')
"""

#%%
def silt_fraction(gdf, raster):
    raster = rxr.open_rasterio(silt_fraction_path / 'mapbiomas-brazil-collection2-beta-000_010cm-granulometry_silt_percent-0000095232-0000063488.tif', band_as_variable=True)
    
    # Definindo CRS
    raster.rio.write_crs("epsg:4326", inplace=True)
    
    # Reduzindo a dimensão do raster 1/10
    downscale_factor = 1/10
        
    # nova largura e altura
    new_width = raster.rio.width * downscale_factor
    new_height = raster.rio.height * downscale_factor
        
    # fazendo o downscaling
    raster = raster.rio.reproject(raster.rio.crs, shape=(int(new_height),
                                                         int(new_width)),
                                  resampling=Resampling.bilinear)
    
    #Designando valores de teor de silte para cada trecho de via
    values = []
    for _, row in gdf.iterrows():
        line = row['geometry']  
    
        if line.geom_type == 'LineString':
            line_values = []  
            """ Para cada ponto na LineString, pega os índices mais próximos e com 
             eles o teor de silte"""
            for point in line.coords:
                lon, lat = point
                lat_idx = np.abs(raster['y'] - lat).argmin()  
                lon_idx = np.abs(raster['x'] - lon).argmin()  
                value = raster['band_1'][lon_idx, lat_idx].values  
                line_values.append(value)
            values.append(line_values)  
    
        else:
            values.append(None)  
    
    
    gdf['silt_fraction'] = values
    gdf.loc[:,'silt_fraction'] = gdf.loc[:,'silt_fraction'].str[0]
    
    del lat, lat_idx, line, line_values,lon,lon_idx,point,row
    
    return gdf
















# %% MÉTODO 2

