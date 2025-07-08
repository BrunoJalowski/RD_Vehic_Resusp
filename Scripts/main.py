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
             'vehicle_count_daily-2025-05-28 00_00_00_to_2025-06-23 00_00_00_'
             'rev1.parquet')

fleet_path = ('/home/brunojalowski/Documentos/RD_Vehic_Resusp/dados_entrada/'
              'FrotapormunicipioetipoDezembro2024.xlsx')

# %% FUNCTIONS

# SOIL MOISTURE
def assign_soil_moisture(gdf, soil_moisture):
    """
    Assigns soil moisture values for each point of each linestring
    
    Args:
        gdf: GeoDataFrame contendo as estradas (LineStrings)
        soil_moisture: Dataset xarray com os valores de umidade do solo
        
    Returns:
        GeoDataFrame with columns for soil moisture values, mean values,
        standard deviation and point count for each road.
    """
    # Initializing arrays
    all_values = []
    means = np.empty(len(gdf))
    stds = np.empty(len(gdf))
    counts = np.empty(len(gdf))
    
    # Obtaining soil moisture dataset coordinates
    soil_lons = soil_moisture['lon'].values
    soil_lats = soil_moisture['lat'].values
    soil_values = soil_moisture.values
    
    for i, line in enumerate(gdf.geometry):
        if line.is_empty:
            all_values.append([])
            means[i] = np.nan
            stds[i] = np.nan
            counts[i] = 0
            continue
            
        # Extracting coordinates from points
        coords = np.array(line.coords)
        lons = coords[:, 0]
        lats = coords[:, 1]
        
        # Finding closest indexes
        lon_idx = np.argmin(np.abs(soil_lons - lons[:, np.newaxis]), axis=1)
        lat_idx = np.argmin(np.abs(soil_lats - lats[:, np.newaxis]), axis=1)
        
        # Obtaining values
        values = soil_values[lat_idx, lon_idx]
        all_values.append(values.tolist())
        
        # Calculating statistics
        means[i] = np.nanmean(values)
        stds[i] = np.nanstd(values)
        counts[i] = len(values)
    
    # Adding to GeoDataFrame
    gdf['soil_moisture'] = all_values
    gdf['soil_mean'] = means
    gdf['soil_std'] = stds
    gdf['point_count'] = counts
    
    return gdf

# SILT FRACTION
def assign_silt_fraction(gdf, raster):
    """
    Assigns silt fraction values for each point of each linestring

    Parameters
    ----------
    gdf : TYPE
        DESCRIPTION.
    raster : TYPE
        DESCRIPTION.

    Returnscc = ds.TEMP.attrs.crs# Set the CRS information obtained above
    ds.rio.write_crs(cc.to_string(), inplace = True)
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
                value = raster['band_1'].values[lat_idx, lon_idx]  
                line_values.append(value)
            values.append(line_values)  
    
        else:
            values.append(None)  
    
    
    gdf['silt_fraction'] = values
    gdf.loc[:,'silt_fraction'] = gdf.loc[:,'silt_fraction'].mean()
    
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
        FLEET COMPOSITION EXCEL SPREADSHEET FOR THE MUNICIPALITY.
    lightduty_weight : int or float, optional
        ESTIMATED LIGHT-DUTY FLEET MEDIAN WEIGHT IN TONS.
        The default is 1.1485.
    heavyduty_weight : int or float, optional
        ESTIMATED HEAVY-DUTY FLEET MEDIAN WEIGHT IN TONS.
        The default is 16.0.
    motorcycle_weight : int or float, optional
        ESTIMATED HEAVY-DUTY FLEET MEDIAN WEIGHT IN TONS.
        The default is 0.128.

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
gdf = gpd.read_parquet(flow_path)
#gdf.to_crs("epsg:4326", inplace=True)

# Variables
adt = gdf['average_daily_vehicle_count']



# %% Road surface reclassification
"""
Classificação atual:
    array(['asphalt', 'paving_stones', 'compacted', None, 'unpaved', 'sett',
       'paved', 'cobblestone', 'metal', 'ground', 'gravel', 'dirt',
       'concrete:plates'], dtype=object)

Reclassificação:
    paved = asphalt, paving_stones,sett, paved, cobblestone, metal,
            concrete:plates
    unpaved = compacted, None, unpaved, ground, gravel, dirt
"""

gdf.loc[(gdf['surface'] == 'asphalt') |
        (gdf['surface'] == 'paving_stones') |
        (gdf['surface'] == 'sett') |
        (gdf['surface'] == 'cobblestone') |
        (gdf['surface'] == 'metal') |
        (gdf['surface'] == 'concrete:plates'),
        'surface'] = 'paved'

gdf.loc[(gdf['surface'] == 'compacted') |
        (gdf['surface'] == 'None') |
        (gdf['surface'] is None) |
        (gdf['surface'] == 'ground') |
        (gdf['surface'] == 'gravel') |
        (gdf['surface'] == 'dirt'), 'surface'] = 'unpaved'

# %% SILT LOADING

""" Silt loading according to Average Daily Traffic (ADT) values from AP-42:
    0     < ADT <   500 --> 0.6
    500   < ADT <  5000 --> 0.2
    5000  < ADT < 10000 --> 0.06
    10000 < ADT < infinity --> 0.03
"""
# Assigning silt loading values by ADT
gdf.loc[(adt < 500) &
        (gdf['surface'] == 'paved'),'silt_loading'] = 0.6

gdf.loc[(adt >= 500) &
        (adt < 5000) &
        (gdf['surface'] == 'paved'),'silt_loading'] = 0.3

gdf.loc[(adt >= 5000) &
        (adt < 10000) &
        (gdf['surface'] == 'paved'),'silt_loading'] = 0.06

gdf.loc[(adt >= 10000) &
        (gdf['surface'] == 'paved'),'silt_loading'] = 0.03


# %% SOIL MOISTURE

# Opening MCIP dataset
xds = xr.open_mfdataset(soil_moisture_path)

# Defining dataset coordinates
xds = conv.brain_to_latlng(xds)

# Locating soil moisture variable
# SOIM1 = volumetric soil moisture in near-surface soil (m3.m-3)
soil_moisture = xds['SOIM1']  

# Assigning soil moisture values to roads
gdf = assign_soil_moisture(gdf, soil_moisture)

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
gdf = assign_silt_fraction(gdf, raster)

# %% VEHICULAR WEIGHT
vehicular_weight = vehicular_weight(fleet_path)


#%%