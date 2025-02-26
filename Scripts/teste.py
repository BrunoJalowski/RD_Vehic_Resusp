#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb 11 11:42:04 2025

@author: brunojalowski
"""
#%%
import geopandas as gpd
from datetime import datetime
import math
import xarray as xr
import rioxarray as rxr
import emission_factors as ef
import matplotlib.pyplot as plt
import netcdf4_conversions_v2 as conv
import numpy as np
#%%
gdf = gpd.read_file('/home/brunojalowski/Documentos/RD_Vehic_Resusp/dados_entrada/4.speed_equation/2025-01-22_01_merged_merged_speed.gpkg')
gdf.columns
"""Index(['index', 'road_type', 'traffic_level', 'traffic_road_coverage',
       'road_category', 'road_subcategory', 'road_closure', 'area_traffic',
       'access', 'bicycle', 'bridge', 'cycleway', 'foot', 'highway',
       'junction', 'lanes', 'lit', 'maxspeed', 'motor_vehi', 'name', 'oneway',
       'overtaking', 'ref', 'service', 'sidewalk', 'smoothness', 'surface',
       'width', 'id', 'timestamp', 'version', 'tags', 'osm_type', 'length',
       'area_index', 'density', 'flow', 'geometry'],
      dtype='object')
"""

#%%Recorte em gdf menor com colunas importantes
gdf_cut = gdf.loc[ : , ['id','timestamp','traffic_level',
                        'length','flow','surface','road_category','geometry'] ]

#%%Conversão timestamp to datetime
gdf_cut.loc[:,'datetime'] = gdf_cut.loc[:,'timestamp'].apply(datetime.fromtimestamp)

#%%Filtragem de flow=Nan
gdf_filtered = gdf_cut.dropna(axis=0)

del gdf, gdf_cut
#%%Arredondar flow para cima
gdf_filtered.loc[:,'flow'] = gdf_filtered.loc[:,'flow'].apply(math.ceil)

#%%Reclassificação superfície das vias
"""
Classificação atual:
    array(['asphalt', 'paving_stones', 'compacted', None, 'unpaved', 'sett',
       'paved', 'cobblestone', 'metal', 'ground', 'gravel', 'dirt',
       'concrete:plates'], dtype=object)

Reclassificação:
    paved = asphalt, paving_stones,sett, paved, cobblestone, metal, concrete:plates
    unpaved = compacted, None, unpaved, ground, gravel, dirt

"""

gdf_filtered.loc[(gdf_filtered['surface'] == 'asphalt') |
                 (gdf_filtered['surface'] == 'paving_stones') |
                 (gdf_filtered['surface'] == 'sett') |
                 (gdf_filtered['surface'] == 'cobblestone') |
                 (gdf_filtered['surface'] == 'metal') |
                 (gdf_filtered['surface'] == 'concrete:plates'), 'surface'] = 'paved'

gdf_filtered.loc[(gdf_filtered['surface'] == 'compacted') |
                 (gdf_filtered['surface'] == 'None') |
                 (gdf_filtered['surface'] ==  None) |
                 (gdf_filtered['surface'] == 'ground') |
                 (gdf_filtered['surface'] == 'gravel') |
                 (gdf_filtered['surface'] == 'dirt'), 'surface'] = 'unpaved'





#%%DADOS DA WRF CMIP DE UMIDADE DO SOLO 

#Abrindo o dataset da WRF
xds = xr.open_mfdataset('/home/brunojalowski/Documentos/RD_Vehic_Resusp/dados_entrada/Soil Moisture/METCRO2D_BR_20km_2023-02-01.nc')
print(xds.dims)

#%%Definição das coordenadas LAT e LON do dataset 
xds = conv.brain_to_latlng(xds) 

#%%Localizar a variável de soil moisture
soil_moisture = xds['SOIM1'] #SOIM1 = volumetric soil moisture in near-surface soil (m3.m-3)

#%%Passando o geodataframe para o mesmo CRS de soil_moisture
gdf_filtered = gdf_filtered.to_crs(soil_moisture.rio.crs)

#%%Plotando os dois para ver se encaixam
fig, ax = plt.subplots()
xr.plot.pcolormesh(darray=soil_moisture[0,0,:,:],ax=ax)
gdf_filtered.plot(ax=ax, color="r")

plt.show()

#%%Designando valores de umidade do solo para cada trecho de via
values = []
for _, row in gdf_filtered.iterrows():
    line = row['geometry']  # Access the LineString geometry

    if line.geom_type == 'LineString':  # Check if the geometry is a LineString
        line_values = []  # List to store pixel values for this LineString
        for point in line.coords:  # Loop through each point in the LineString
            lon, lat = point
            lat_idx = np.abs(soil_moisture['lat'] - lat).argmin()  # Nearest latitude index
            lon_idx = np.abs(soil_moisture['lon'] - lon).argmin()  # Nearest longitude index
            value = soil_moisture[0,0, lat_idx, lon_idx].values  # Get pixel value (for all times)
            line_values.append(value)
        values.append(line_values)  # Add the pixel values of the current line to the list

    else:
        values.append(None)  # If it's not a LineString, append None


gdf_filtered['soil_moisture'] = values
gdf_filtered.loc[:,'soil_moisture'] = gdf_filtered.loc[:,'soil_moisture'].str[0]

del lat, lat_idx, line, line_values,lon,lon_idx,point,row

#%%Dados iniciais via não pavimentada
silt_fraction = 1
pm = 2.5


#%%Fator de emissão PM2.5 por trecho de via não pavimentada de acesso público em lb/VMT
gdf_filtered.loc[gdf_filtered['surface']=='unpaved','EF_unpaved'] = ef.emission_unpaved_public(pm, silt_fraction, (gdf_filtered.loc[:,'traffic_level'] * 0.621371), gdf_filtered.loc[:,'soil_moisture'])

# 0.621371 é o fator de conversão de km/h para mph

#%%Conversão de lb/VMT para g/VKT
gdf_filtered.loc[gdf_filtered['surface']=='unpaved','EF_unpaved'] = gdf_filtered.loc[:,'EF_unpaved'].apply(ef.lbvmt_to_gvkt)

#%%Correção da emissão pela pluviosidade
gdf_filtered.loc[gdf_filtered['surface']=='unpaved','EF_unpaved_corrected'] = ef.paved_rainfall_correction(gdf_filtered['EF_unpaved'], 100, 365)

#%%Emissão de Pm2.5 por trecho de via
gdf_filtered.loc[gdf_filtered['surface']=='unpaved','emission'] = gdf_filtered.loc[gdf_filtered['surface']=='unpaved','flow'] * gdf_filtered.loc[gdf_filtered['surface']=='unpaved','length']/1000 * gdf_filtered.loc[gdf_filtered['surface']=='unpaved','EF_unpaved_corrected'] 

#%%Plotando para ver localização das vias nao pavimentadas
fig, ax = plt.subplots()
xr.plot.pcolormesh(darray=soil_moisture[0,0,:,:],ax=ax)
gdf_filtered.loc[gdf_filtered['surface']=='unpaved',:].plot(ax=ax, color="r")

plt.show()

"""Ao menos na amostra, as vias pavimentadas se apresentam como maioria no litoral.
Desse modo, talvez essa resolução espacial utilizada não afete muito a estimativa das
emissoes em vias nao pavimentadas, já que só elas que usam umidade do solo"""








#%%










