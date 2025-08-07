#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb 11 11:42:04 2025

@author: brunojalowski
"""
# %%
import geopandas as gpd
import pandas as pd
import xarray as xr
import netcdf4_conversions_v2 as conv
import numpy as np
from pathlib import Path
from rasterio.enums import Resampling
import rioxarray as rxr
from shapely.geometry import box, LineString
import time
from vehicular_weight import vehicular_weight

# %% Paths
project_path = Path('/home/brunojalowski/Documentos/RD_Vehic_Resusp/'
                    'dados_entrada')
soil_moisture_path = (project_path /
                      'Soil Moisture/METCRO2D_BR_20km_2023-02-01.nc')
silt_fraction_path = (project_path /
                      'Silt_Fraction')
flow_path = (project_path /
             'vehicle_count_daily-2025-07-09 00:00:00_to_2025-07-10 00:00:00'
             '_rev1.parquet')

fleet_path = ('/home/brunojalowski/Documentos/RD_Vehic_Resusp/dados_entrada/'
              'FrotapormunicipioetipoDezembro2024.xlsx')

# %% FUNCTIONS

# SOIL MOISTURE
def assigning_soil_moisture(line: LineString,
                            grid: gpd.GeoDataFrame) -> float:
    """
    Calculates the average soil moisture value for each road segment weighted
    by the length inside each pixel.

    Parameters
    ----------
    line : LineString
        ROAD SEGMENT FROM ROAD VECTOR DATAFRAME.
    grid : gpd.GeoDataFrame
        VECTOR GRID MADE FROM VECTORIZING RASTER/XARRAY.

    Returns
    -------
    float
        WEIGHTED AVERAGE FOR SOIL MOISTURE.

    """
    
    # Selects only cells that intersect with the linestring
    intersected_cells = grid[grid.intersects(line)].copy()
    if intersected_cells.empty:
        return np.nan
    
    # Gets line total length
    intersected_cells["total_length"] = (line
                                         .length)
    
    # Gets length of line inside each cell
    intersected_cells["intersected_length"] = (intersected_cells
                                               .geometry
                                               .intersection(line)
                                               .length)
    
    # Weight factor
    intersected_cells["weight_factor"] = (
        intersected_cells["intersected_length"] /
        intersected_cells["total_length"]
        )
    
    # Soil moisture weighted average
    weighted_average = (
        intersected_cells['weight_factor'] *
        intersected_cells['value']
        ).sum()
    
    return weighted_average


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
            """For each LineString, rIndustrial_Sites import roads_template as gdfeturns the closest indexes and with them, 
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
from road_preprocess import gdf

# %% INDUSTRIAL SITES AND SILT LOADING
from Industrial_Sites import roads_template

# Applying segmentation and silt loading values for every timestep
gdf = gdf.merge(roads_template, how='left', on='osm_id')

# Dropping road geometry and setting segment geometry column as default
gdf = gpd.GeoDataFrame(gdf, geometry='geometry_y')
gdf = gdf.drop(columns=['geometry_x', 'geometry_y'])

# Simplifying column names into variables
adt = gdf['average_daily_vehicle_count']

# Silt loading for road segments outside buffers
""" Silt loading according to Average Daily Traffic (ADT) values from AP-42:
        0 < ADT <   500 --> 0.6
      500 < ADT <  5000 --> 0.2
     5000 < ADT < 10000 --> 0.06
    10000 < ADT < infinity --> 0.03
"""
# Assigning silt loading values by ADT
gdf.loc[(gdf['silt_loading'].isna()) &
        (adt < 500) &
        (gdf['surface'] == 'paved'),'silt_loading'] = 0.6

gdf.loc[(gdf['silt_loading'].isna()) &
        (adt >= 500) &
        (adt < 5000) &
        (gdf['surface'] == 'paved'),'silt_loading'] = 0.3

gdf.loc[(gdf['silt_loading'].isna()) &
        (adt >= 5000) &
        (adt < 10000) &
        (gdf['surface'] == 'paved'),'silt_loading'] = 0.06

gdf.loc[(gdf['silt_loading'].isna()) &
        (adt >= 10000) &
        (gdf['surface'] == 'paved'),'silt_loading'] = 0.03


# Subclassifying unpaved roads in industrial or open access
gdf.loc[(gdf['silt_loading'].notna()) &
        (gdf['surface'] == 'unpaved'), 'subcategory'] = 'industrial'

gdf.loc[(gdf['silt_loading'].isna()) &
        (gdf['surface'] == 'unpaved'), 'subcategory'] = 'open access'

gdf.loc[gdf['surface'] == 'paved', 'subcategory'] = 'paved'


# Removing silt loading values from unpaved segments inside industrial zones
gdf.loc[(gdf['silt_loading'].notna()) &
        (gdf['surface'] == 'unpaved'), 'silt_loading'] = None

# %% SOIL MOISTURE
s = time.time()

# Opening MCIP dataset
xds = xr.open_mfdataset(soil_moisture_path)

# Defining dataset coordinates
xds = conv.brain_to_latlng(xds)

# Locating soil moisture variable
# SOIM1 = volumetric soil moisture in near-surface soil (m3.m-3)
soil_moisture = xds['SOIM1']  
del xds

# --------------------------
# Pixels' centroids from soil_moisture
lons = soil_moisture['lon'].values
lats = soil_moisture['lat'].values

# Calculates halfways between centroids
lon_edges = np.concatenate([
    [lons[0] - (lons[1] - lons[0]) / 2],
    (lons[:-1] + lons[1:]) / 2,
    [lons[-1] + (lons[-1] - lons[-2]) / 2]
])

lat_edges = np.concatenate([
    [lats[0] - (lats[1] - lats[0]) / 2],
    (lats[:-1] + lats[1:]) / 2,
    [lats[-1] + (lats[-1] - lats[-2]) / 2]
])

# Creates grid cells based on the edges coordinates
grid_cells = []
i_indexes = []
j_indexes = []
for i in range(len(lat_edges) - 1):
    for j in range(len(lon_edges) - 1):
        cell = box(
            lon_edges[j],
            lat_edges[i],
            lon_edges[j + 1],
            lat_edges[i + 1]
        )
        grid_cells.append(cell)
        i_indexes.append(i)
        j_indexes.append(j)

del i, j, cell

# Turns it into a GeoDataFrame
soil_grid = gpd.GeoDataFrame(geometry=grid_cells, crs="EPSG:4326")
soil_grid['i_index'] = i_indexes
soil_grid['j_index'] = j_indexes

# Deleting variables
del i_indexes, j_indexes

# Get the soil moisture values as a 2D array
values = soil_moisture.isel(TSTEP=0,LAY=0).values

# Map the values to the grid cells
soil_grid['value'] = [values[i, j] 
                      for i, j 
                      in zip(soil_grid['i_index'], soil_grid['j_index'])]

# Drop the indices
soil_grid = soil_grid.drop(columns=['i_index', 'j_index'])

# -------------------------------------------------
# Assigning soil moisture values to each road
values = []
for ii in range(gdf.shape[0]):
        line = gdf.geometry.iloc[ii]
        value = assigning_soil_moisture(line, soil_grid)
        if value > 0 :
            values.append(value)
        else:
            values.append(None)

gdf['soil_moisture'] = values
del value, values, ii

# Checking duration time
soil_moisture_time = time.time() - s

# %% SILT FRACTION
s = time.time()
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

# Checking duration time
silt_fraction_time = time.time() - s

# %% VEHICULAR WEIGHT
vehicular_weight = vehicular_weight(fleet_path)


#%%