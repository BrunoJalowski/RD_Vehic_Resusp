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
import netcdf4_conversions_v2 as conv
import numpy as np
from pathlib import Path
import glob
from rasterio.enums import Resampling
import rioxarray as rxr

#%% Paths
project_path = Path('/home/brunojalowski/Documentos/RD_Vehic_Resusp/dados_entrada')
soil_moisture_path = project_path / 'Soil Moisture/METCRO2D_BR_20km_2023-02-01.nc'
silt_fraction_path = project_path /'Silt_Fraction'
flow_path = project_path / '4.speed_equation' 


#%% FUNCTIONS
def soil_moisture(gdf,soil_moisture_path):
    """Assigns soil moisture values for each linestring segment

    Args:
        gdf (GeoDataFrame): GeoDataFrame with linestrings

        soil_moisture_path (str): path for oil moisture dataset

    Returns:
        float: soil moisture content (%)
    """
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
                line_values.append(value * 100)
            values.append(line_values)  
    
        else:
            values.append(None)  
    
    
    gdf['soil_moisture'] = values
    gdf.loc[:,'soil_moisture'] = gdf.loc[:,'soil_moisture'].str[0]
    
    del lat, lat_idx, line, line_values,lon,lon_idx,point,row

    return gdf 



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


#%% FLOW AND SPEED DATA FROM TOMTOM

# Reading geodataframe
files = glob.glob(str(flow_path / '*.gpkg'))
gdf = gpd.read_file(files[0])
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

#%% Filtering important columns from the gdf
gdf_cut = gdf.loc[ : , ['id','timestamp','traffic_level',
                        'length','flow','surface','road_category','geometry'] ]

#%% Sorting rows by timestamp values
gdf_cut = gdf_cut.sort_values(by=['timestamp'])
#%% Converting timestamp to datetime
gdf_cut.loc[:,'datetime'] = gdf_cut.loc[:,'timestamp'].apply(datetime.fromtimestamp)

#%% Filtering Flow = Nan
gdf_filtered = gdf_cut.dropna(axis=0)

del gdf, gdf_cut
#%% Rounding up flow values
gdf_filtered.loc[:,'flow'] = gdf_filtered.loc[:,'flow'].apply(math.ceil)

#%% Road surface reclassification
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
    0     < ADT <   500 --> 0.6
    500   < ADT <  5000 --> 0.2
    5000  < ADT < 10000 --> 0.06
    10000 < ADT < infinity --> 0.03
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
    silt_values[flow_values < key] = value

# Assigning the silt loading values 
gdf_filtered['silt_loading'] = silt_values

del flow_values, silt_values, key, value, adt

#%% UMIDADE DO SOLO
gdf_filtered = soil_moisture(gdf_filtered, soil_moisture_path)

#%% SILT FRACTION
gdf_filtered = silt_fraction(gdf_filtered, silt_fraction_path)
