#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul  8 12:30:38 2025

@author: brunojalowski
"""
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

# %% PATHS
project_path = Path('/home/brunojalowski/Documentos/RD_Vehic_Resusp/'
                    'dados_entrada')

flow_path = (project_path /
             'vehicle_count_daily-2025-07-09 00:00:00_to_2025-07-10 '
             '00:00:00_rev1.parquet')

# %% FLOW AND SPEED DATA FROM TOMTOM

# Reading geodataframe
gdf = (gpd
       .read_parquet(path=flow_path)
       .astype({'osm_id': int,
                'vehicle_count': float,
                'average_daily_vehicle_count': float,
                'road_length': float,
                'vkt_per_hour': float,
                'surface': str,
                'avg_traffic_level': float}))

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
"""difference = geoms_for_intersect_02.difference(geoms_for_intersect_01)
# Assigning silt loading values by ADT
gdf.loc[(adt < 500) &
        (gdf['surface'] == 'paved'),'silt_loading'] = difference = geoms_for_intersect_02.difference(geoms_for_intersect_01)0.6

gdf.loc[(adt >= 500) &
        (adt < 5000) &
        (gdf['surface'] == 'paved'),'silt_loading'] = 0.3

gdf.loc[(adt >= 5000) &
        (adt < 10000) &
        (gdf['surface'] == 'paved'),'silt_loading'] = 0.06

gdf.loc[(adt >= 10000) &
        (gdf['surface'] == 'paved'),'silt_loading'] = 0.03

