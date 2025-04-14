#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar 21 11:17:19 2025

@author: brunojalowski

Dados de umidade do solo do CMIP da WRF. 
A variável de interesse é SOIM1 = volumetric soil moisture in near-surface soil (m3.m-3).

"""
#%% Importando pacotes
import xarray as xr
import matplotlib.pyplot as plt
import netcdf4_conversions_v2 as conv
import numpy as np
from main import gdf_filtered

#%%Abrindo o dataset da WRF
xds = xr.open_mfdataset('/home/brunojalowski/Documentos/RD_Vehic_Resusp/dados_entrada/Soil Moisture/METCRO2D_BR_20km_2023-02-01.nc')
print(xds.dims)

#%%Definição das coordenadas LAT e LON do dataset 
xds = conv.brain_to_latlng(xds) 

#%%Localizar a variável de soil moisture
soil_moisture = xds['SOIM1'] #SOIM1 = volumetric soil moisture in near-surface soil (m3.m-3)

#%%Passando o geodataframe para o mesmo CRS de soil_moisture
gdf_filtered = gdf_filtered.to_crs(soil_moisture.rio.crs)

#%%Plotando os dois para ver se encaixam
"""
fig, ax = plt.subplots()
xr.plot.pcolormesh(darray=soil_moisture[0,0,:,:],ax=ax)
gdf_filtered.plot(ax=ax, color="r")

plt.show()
"""

#%%Designando valores de umidade do solo para cada trecho de via
values = []
for _, row in gdf_filtered.iterrows():
    line = row['geometry']  

    if line.geom_type == 'LineString':
        line_values = []  
        """ Para cada ponto na LineString, pega os índices mais próximos e com 
         eles o valor de umidade"""
        for point in line.coords:
            lon, lat = point
            lat_idx = np.abs(soil_moisture['lat'] - lat).argmin()  
            lon_idx = np.abs(soil_moisture['lon'] - lon).argmin()  
            value = soil_moisture[0,0, lat_idx, lon_idx].values  
            line_values.append(value*100)
        values.append(line_values)  

    else:
        values.append(None)  


gdf_filtered['soil_moisture'] = values
gdf_filtered.loc[:,'soil_moisture'] = gdf_filtered.loc[:,'soil_moisture'].str[0]

del lat, lat_idx, line, line_values,lon,lon_idx,point,row





#%%Plotando para ver localização das vias nao pavimentadas
"""fig, ax = plt.subplots()
xr.plot.pcolormesh(darray=soil_moisture[0,0,:,:],ax=ax)
gdf_filtered.loc[gdf_filtered['surface']=='unpaved',:].plot(ax=ax, color="r")

plt.show()"""

"""Ao menos na amostra, as vias pavimentadas se apresentam como maioria no litoral.
Desse modo, talvez essa resolução espacial utilizada não afete muito a estimativa das
emissoes em vias nao pavimentadas, já que só elas que usam umidade do solo"""

#%% Assignment results
"""
fig, ax = plt.subplots(figsize=(10, 10))
xr.plot.pcolormesh(darray=soil_moisture[0,0,:,:],ax=ax, alpha=0.5)
gdf_filtered.plot(column='soil_moisture', ax=ax, cmap='hot_r')  

minx, miny, maxx, maxy = gdf_filtered.total_bounds
ax.set_xlim(minx-0.01, maxx+0.01)
ax.set_ylim(miny-0.01, maxy+0.01)

ax.set_title('Soil moisture by road')
ax.set_xlabel('Longitude')
ax.set_ylabel('Latitude')
"""


#%%

def soil_moisture(gdf,xds):
    #Abrindo o dataset do CMIP
    xds = xr.open_mfdataset('/home/brunojalowski/Documentos/RD_Vehic_Resusp/dados_entrada/Soil Moisture/METCRO2D_BR_20km_2023-02-01.nc')
        
    #Definição das coordenadas LAT e LON do dataset 
    xds = conv.brain_to_latlng(xds) 
    
    #Localizar a variável de soil moisture
    soil_moisture = xds['SOIM1'] #SOIM1 = volumetric soil moisture in near-surface soil (m3.m-3)
    
    #Passando o geodataframe para o mesmo CRS de soil_moisture
    gdf = gdf.to_crs(soil_moisture.rio.crs)
    
    
    #Designando valores de umidade do solo para cada trecho de via
    values = []
    for _, row in gdf.iterrows():
        line = row['geometry']  
    
        if line.geom_type == 'LineString':
            line_values = []  
            """ Para cada ponto na LineString, pega os índices mais próximos e com 
             eles o valor de umidade"""
            for point in line.coords:
                lon, lat = point
                lat_idx = np.abs(soil_moisture['lat'] - lat).argmin()  
                lon_idx = np.abs(soil_moisture['lon'] - lon).argmin()  
                value = soil_moisture[0,0, lat_idx, lon_idx].values  
                line_values.append(value * 100)
            values.append(line_values)  
    
        else:
            values.append(None)  
    
    
    gdf['soil_moisture'] = values
    gdf.loc[:,'soil_moisture'] = gdf.loc[:,'soil_moisture'].str[0]
    
    del lat, lat_idx, line, line_values,lon,lon_idx,point,row
    
    return gdf 