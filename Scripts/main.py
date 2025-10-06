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
import rioxarray as rxr
from shapely.geometry import box, LineString
from vehicular_weight import vehicular_weight
import glob
import shapely
from rasterio.features import geometry_mask
from reclassify_surface import reclassify_surface
from silt_loading_by_adt import silt_loading_by_adt
from assign_soil_moisture import assign_soil_moisture
from assign_silt_fraction import assign_silt_fraction

# %% Paths ===================================================================
project_path = Path('/home/brunojalowski/Documentos/RD_Vehic_Resusp/dados_entrada')
#project_path = Path(r"C:\Users\bruno\Desktop\LCQAr\RD_Vehic_Resusp\dados_entrada")

soil_moisture_path = (project_path /
                      'Soil Moisture/METCRO2D_BR_20km_2023-02-01.nc')
silt_fraction_path = project_path / 'Silt_Fraction'
flow_path = (project_path /
             'vehicle_count_daily-2025-07-09 00:00:00_to_2025-07-10 00:00:00'
             '_rev1.parquet')

fleet_path = ('/home/brunojalowski/Documentos/RD_Vehic_Resusp/dados_entrada/'
              'FrotapormunicipioetipoDezembro2024.xlsx')

# %% FLOW AND SPEED DATA FROM TOMTOM

# Reading geodataframe
gdf = (gpd
       .read_parquet(path=flow_path)
       .astype({'osm_id': int,
                'vehicle_count': float,
                'average_daily_vehicle_count': float,
                'vkt_per_hour': float,
                'surface': str,
                'avg_traffic_level': float}))

# Removing datetime column as index
gdf.reset_index(drop=False,
                inplace=True)

# %% Road Preprocessing ======================================================
gdf = reclassify_surface(gdf)

# %% INDUSTRIAL SITES AND SILT LOADING =======================================
from road_segments import roads_template

# Applying segmentation and silt loading values for every timestep
gdf = gdf.merge(roads_template, how='left', on='osm_id')

# Dropping road geometry and setting segment geometry column as default
gdf = gdf.drop(columns=['geometry_x'])
gdf = gdf.rename(columns={'geometry_y':'geometry'})
gdf = gpd.GeoDataFrame(gdf, geometry='geometry')

# Silt loading for road segments outside buffers
gdf = silt_loading_by_adt(gdf)


# Subclassifying unpaved roads in industrial or open access
gdf.loc[(gdf['silt_loading'].notna()) &
        (gdf['surface'] == 'unpaved'), 'subcategory'] = 'industrial'

gdf.loc[(gdf['silt_loading'].isna()) &
        (gdf['surface'] == 'unpaved'), 'subcategory'] = 'open access'

gdf.loc[gdf['surface'] == 'paved', 'subcategory'] = 'paved'


# Removing silt loading values from unpaved segments inside industrial zones
gdf.loc[(gdf['silt_loading'].notna()) &
        (gdf['surface'] == 'unpaved'), 'silt_loading'] = None


# %% SILT FRACTION ===========================================================
# Opening file
files = glob.glob(str(silt_fraction_path / '*.tif'))

for idx,file in enumerate(files):
    # Opening raster
    raster = rxr.open_rasterio(file, band_as_variable=True)  
    # Assigning CRS
    raster.rio.write_crs("epsg:4326", inplace=True)
    break
    mask = geometry_mask(
        geometries=gdf.geometry,
        transform=raster.band_1.rio.transform(),
        invert=True, 
        out_shape=raster.band_1.shape
    )
    
    masked_raster = raster.band_1.where(mask)

    pixel_values = masked_raster.values
    
    inside_pixels = pixel_values[~np.isnan(pixel_values)]
    
    break

#     
#     # Assigning CRS
#     raster.rio.write_crs("epsg:4326", inplace=True)
#     
#     # Getting raster bounds
#     #raster_bbox = box(*raster.rio.bounds()).exterior.xy
#     
#     # Pixels' centroids
#     lons = raster['x'].values
#     lats = raster['y'].values
#     
#     # Calculates halfways between centroids
#     lon_edges = np.concatenate([
#         [lons[0] - (lons[1] - lons[0]) / 2],
#         (lons[:-1] + lons[1:]) / 2,
#         [lons[-1] + (lons[-1] - lons[-2]) / 2]
#     ])
# 
#     lat_edges = np.concatenate([
#         [lats[0] - (lats[1] - lats[0]) / 2],
#         (lats[:-1] + lats[1:]) / 2,
#         [lats[-1] + (lats[-1] - lats[-2]) / 2]
#     ])
# 
#     # Creates grid cells based on the edges coordinates
#     grid_cells = []
#     i_indexes = []
#     j_indexes = []
#     for i in range(len(lat_edges) - 1):
#         for j in range(len(lon_edges) - 1):
#             cell = box(
#                 lon_edges[j],
#                 lat_edges[i],
#                 lon_edges[j + 1],
#                 lat_edges[i + 1]
#             )
#             grid_cells.append(cell)
#             i_indexes.append(i)
#             j_indexes.append(j)
# 
#     del i, j, cell
#     
#     # Turns it into a GeoDataFrame
#     silt_grid = gpd.GeoDataFrame(geometry=grid_cells, crs="EPSG:4326")
#     silt_grid['i_index'] = i_indexes
#     silt_grid['j_index'] = j_indexes
#     
#     # Deleting variables
#     del i_indexes, j_indexes
# 
#     # Get the soil moisture values as a 2D array
#     values = raster.band_1.values
# 
#     # Map the values to the grid cells
#     silt_grid['value'] = [values[i, j] 
#                           for i, j 
#                           in zip(silt_grid['i_index'], silt_grid['j_index'])]
# 
#     # Drop the indices
#     silt_grid = silt_grid.drop(columns=['i_index', 'j_index'])
#     
#     grid_list.append(silt_grid)
# 
# silt_grid = pd.concat(grid_list)
# =============================================================================

# Assigning silt fraction values to unpaved roads
gdf = assign_silt_fraction(gdf, raster)

# %% SOIL MOISTURE
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
        value = assign_soil_moisture(line, soil_grid)
        if value > 0 :
            values.append(value)
        else:
            values.append(None)

gdf['soil_moisture'] = values
del value, values, ii

