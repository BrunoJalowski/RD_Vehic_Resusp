#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb 11 11:42:04 2025

@author: brunojalowski
"""
# %%
import geopandas as gpd
import pandas as pd
from datetime import datetime
import math
import xarray as xr
import netcdf4_conversions_v2 as conv
import numpy as np
from pathlib import Path
import glob
from rasterio.enums import Resampling
import rioxarray as rxr
import regex as re

# %% Paths
project_path = Path('/home/brunojalowski/Documentos/RD_Vehic_Resusp/'
                    'dados_entrada')
soil_moisture_path = (project_path /
                      'Soil Moisture/METCRO2D_BR_20km_2023-02-01.nc')
silt_fraction_path = (project_path /
                      'Silt_Fraction')
flow_path = (project_path /
             'vehicle_count_daily-2025-05-28 00_00_00_'
             'to_2025-06-23 00_00_0.csv')

fleet_path = ('/home/brunojalowski/Documentos/RD_Vehic_Resusp/dados_entrada/'
              'FrotapormunicipioetipoDezembro2024.xlsx')

# %% FUNCTIONS

# SOIL MOISTURE
def assign_soil_moisture(gdf, soil_moisture):
    """Assigns soil moisture values for each linestring segment

    Args:
        gdf (GeoDataFrame): GeoDataFrame with linestrings

        soil_moisture (Dataset): soil moisture dataset

    Returns:
        float: soil moisture content (%)
    """
    # Passando o geodataframe para o mesmo CRS de soil_moisture
    gdf = gdf.to_crs(soil_moisture.rio.crs)

    # Designando valores de umidade do solo para cada trecho de via
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


# SILT FRACTION
def assign_silt_fraction(gdf, raster):
    """
    

    Parameters
    ----------
    gdf : TYPE
        DESCRIPTION.
    raster : TYPE
        DESCRIPTION.

    Returns
    -------
    gdf : TYPE
        DESCRIPTION.

    """   
    #Designando valores de teor de silte para cada trecho de via
    values = []
    for _, row in gdf.iterrows():
        line = row['geometry']  
    
        if line.geom_type == 'LineString':
            line_values = []  
            """For each LineString, returns the closest indexes and with them, 
            the silt fraction values"""
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

# VEHICULAR WEIGHT
def vehicular_weight(fleet_path: str,
                     light_duty_weight = 1.1485,
                     heavy_duty_weight = 16.0,
                     motorcycle_weight = 0.128):
    """
    This function calculates de average vehicular weight for each city based 
    on fleet composition and median weight for each vehicle category

    Parameters
    ----------
    fleet_path : str
        DESCRIPTION.
    lightduty_weight : int or float, optional
        DESCRIPTION. The default is 1.1485.
    heavyduty_weight : int or float, optional
        DESCRIPTION. The default is 16.0.
    motorcycle_weight : int or float, optional
        DESCRIPTION. The default is 0.128.

    Returns
    -------
    df : TYPE
        DESCRIPTION.

    """
    # Reading file containing vehicle fleet
    df = pd.read_excel(fleet_path, skiprows=3)

    # Reclassifying vehicles
    df['light_duty'] = df.loc[:, ['AUTOMOVEL',
                             'BONDE',
                             'CAMINHONETE',
                             'CAMIONETA',
                             'UTILITARIO',
                             'OUTROS']].sum(1)

    df['motorcycles'] = df.loc[:, ['CICLOMOTOR',
                                    'MOTOCICLETA',
                                    'MOTONETA',
                                    'QUADRICICLO',
                                    'SIDE-CAR',
                                    'TRICICLO']].sum(1)

    df['heavy_duty'] = df.loc[:, ['CAMINHAO',
                               'CAMINHAO TRATOR',
                               'CHASSI PLATAF',
                               'MICRO-ONIBUS',
                               'ONIBUS',
                               'REBOQUE',
                               'SEMI-REBOQUE',
                               'TRATOR ESTEI',
                               'TRATOR RODAS']].sum(1)

        # Calculating mean_weight for each city
    df['average_weight'] = ((df.loc[:, 'light_duty'] * light_duty_weight +
                             df.loc[:, 'motorcycles'] * motorcycle_weight +
                             df.loc[:, 'heavy_duty'] * heavy_duty_weight) /
                            df.loc[:, 'TOTAL'])

    return df

# %% FLOW AND SPEED DATA FROM TOMTOM

# Reading geodataframe
files = glob.glob(str(flow_path / '*.gpkg'))

gdf = gpd.GeoDataFrame()
for file in files:
    add = gpd.read_file(file)
    add['datetime'] = re.findall(r'([\d]{4}\-[\d]{2}\-[\d]{2}_[\d]{2})',
                                 file)[0]
    gdf = pd.concat([gdf, add])

del add, file, files
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

# %% Filtering important columns from the gdf
gdf_cut = gdf.loc[:, ['datetime','id', 'traffic_level', 'length', 'flow',
                      'surface', 'road_category', 'geometry']]

# %% Filtering Flow = Nan
gdf_filtered = gdf_cut.dropna(axis=0)
del gdf, gdf_cut

# %% Formatting datetime and setting as index
gdf_filtered['datetime'] = gdf_filtered['datetime'].replace('_',
                                                            ' ',
                                                            regex=True)

gdf_filtered['datetime'] = pd.to_datetime(gdf_filtered['datetime'],
                                          format='%Y-%m-%d %H')

gdf_filtered.set_index('datetime', inplace=True)
# %% Road surface reclassification
"""
Classificação atual:
    array(['asphalt', 'paving_stones', 'compacted', None, 'unpaved', 'sett',
       'paved', 'cobblestone', 'metal', 'ground', 'gravel', 'dirt',
       'concrete:plates'], dtype=object)

Reclassificação:
    paved = asphalt, paving_stones,sett, paved, cobblestone, metal,
            concrete:plates
    unpaved = compacted, None, unpaved, groun,
                                  left_on=Trued, gravel, dirt

"""

gdf_filtered.loc[(gdf_filtered['surface'] == 'asphalt') |
                 (gdf_filtered['surface'] == 'paving_stones') |
                 (gdf_filtered['surface'] == 'sett') |
                 (gdf_filtered['surface'] == 'cobblestone') |
                 (gdf_filtered['surface'] == 'metal') |
                 (gdf_filtered['surface'] == 'concrete:plates'),
                 'surface'] = 'paved'

gdf_filtered.loc[(gdf_filtered['surface'] == 'compacted') |
                 (gdf_filtered['surface'] == 'None') |
                 (gdf_filtered['surface'] is None) |
                 (gdf_filtered['surface'] == 'ground') |
                 (gdf_filtered['surface'] == 'gravel') |
                 (gdf_filtered['surface'] == 'dirt'), 'surface'] = 'unpaved'

# %% AVERAGE DAILY TRAFFIC

# Calculating ADT for each road
adt_df = pd.DataFrame()
adt_df['adt'] = gdf_filtered['flow'].resample('D').mean()

# Creating temporary columns for merge by date
adt_df['date'] = adt_df.index.date
gdf_filtered['date'] = gdf_filtered.index.date
index = gdf_filtered.index

# Applying ADT value for each day
gdf_filtered = gdf_filtered.merge(adt_df,
                                  how='inner',
                                  on='date')

gdf_filtered = gdf_filtered.set_index(index)

# Dropping temporary columns
gdf_filtered.drop(['date'], axis=1, inplace=True)

# %% SILT LOADING
""" Silt loading according to Average Daily Traffic (ADT) values from AP-42:
    0     < ADT <   500 --> 0.6
    500   < ADT <  5000 --> 0.2
    5000  < ADT < 10000 --> 0.06
    10000 < ADT < infinity --> 0.03
"""
# Assigning silt loading values from ADT
gdf_filtered.loc[(gdf_filtered['adt'] < 500) &
                 (gdf_filtered['surface'] == 'paved'),'silt_loading'] = 0.6

gdf_filtered.loc[(gdf_filtered['adt'] >= 500) &
                 (gdf_filtered['adt'] < 5000) &
                 (gdf_filtered['surface'] == 'paved'),'silt_loading'] = 0.3

gdf_filtered.loc[(gdf_filtered['adt'] >= 5000) &
                 (gdf_filtered['adt'] < 10000) &
                 (gdf_filtered['surface'] == 'paved'),'silt_loading'] = 0.06

gdf_filtered.loc[(gdf_filtered['adt'] >= 10000) &
                 (gdf_filtered['surface'] == 'paved'),'silt_loading'] = 0.03


# %% SOIL MOISTURE

# Opening MCIP dataset
xds = xr.open_mfdataset(soil_moisture_path)

# Defining dataset coordinates
xds = conv.brain_to_latlng(xds)

# Locating soil moisture variable
# SOIM1 = volumetric soil moisture in near-surface soil (m3.m-3)
soil_moisture = xds['SOIM1']  

# Assigning soil moisture values to roads
gdf_filtered = assign_soil_moisture(gdf_filtered, soil_moisture)

# %% SILT FRACTION

# Opening silt_fraction raster
raster = rxr.open_rasterio(silt_fraction_path / 'mapbiomas-brazil-collection2-beta-000_010cm-granulometry_silt_percent-0000095232-0000063488.tif', band_as_variable=True)

# Assigning CRS
raster.rio.write_crs("epsg:4326", inplace=True)

# Downscaling factor
downscale_factor = 1/10
    
# new width and height
new_width = raster.rio.width * downscale_factor
new_height = raster.rio.height * downscale_factor
    
# Downscaling
raster = raster.rio.reproject(raster.rio.crs, shape=(int(new_height),
                                                     int(new_width)),
                              resampling=Resampling.bilinear)

# Assigning silt fraction values to unpaved roads
gdf_filtered = assign_silt_fraction(gdf_filtered, raster)

# %% VEHICULAR WEIGHT
vehicular_weight = vehicular_weight(fleet_path)







#%%