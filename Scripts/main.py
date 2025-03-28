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
import rasterio
from pathlib import Path


#%% Paths
project_path = Path('/home/brunojalowski/Documentos/RD_Vehic_Resusp/dados_entrada')
soil_moisture_path = project_path / 'Soil Moisture/METCRO2D_BR_20km_2023-02-01.nc'
silt_fraction_path = project_path /'MAPBIOMAS-EXPORT-20250220T123349Z-001/MAPBIOMAS-EXPORT/mapbiomas-brazil-collection-beta-2021-cos_0_30cm_kg_m2-0000000000-0000158720.tif'
flow_path = project_path / '4.speed_equation/2025-01-22_01_merged_merged_speed.gpkg'

#%% FUNCTIONS
def soil_moisture(gdf,soil_moisture_path):
    #Abrindo o dataset do CMIP
    xds = xr.open_mfdataset(soil_moisture_path)
        
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
                line_values.append(value)
            values.append(line_values)  
    
        else:
            values.append(None)  
    
    
    gdf['soil_moisture'] = values
    gdf.loc[:,'soil_moisture'] = gdf.loc[:,'soil_moisture'].str[0]
    
    del lat, lat_idx, line, line_values,lon,lon_idx,point,row

    return gdf 



#%%Dados de velocidade do Tomtom combinado com dados de fluxo 
gdf = gpd.read_file(flow_path)
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



#%% SILT LOADING
""" Silt loading according to Average Daily Traffic (ADT) values from AP-42 "Paved Roads":
            ADT <   500 --> 0.6
    500   < ADT <  5000 --> 0.2
    5000  < ADT < 10000 --> 0.06
    10000 < ADT < infinity  --> 0.03
    """
adt = {500:0.6,
       5000:0.3,
       10000:0.06,
       100000000:0.03}

# Creating the silt loading column
gdf_filtered.loc[:,'silt_loading'] = gdf_filtered.loc[:,'flow']

# Creating list with flow and silt loading values
flow_values = gdf_filtered['flow'].values
silt_values = gdf_filtered['silt_loading'].values

# Filtering silt loading values according to the flow column
for key, value in sorted(adt.items(),reverse=True):
    silt_values[flow_values <= float(key)] = value

# Assigning the silt loading values 
gdf_filtered['silt_loading'] = silt_values



#%% UMIDADE DO SOLO

gdf_filtered = soil_moisture(gdf_filtered, soil_moisture_path)

#%%
