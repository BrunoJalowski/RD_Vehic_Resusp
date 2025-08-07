#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul  8 12:30:38 2025

@author: brunojalowski
"""
import geopandas as gpd
from pathlib import Path

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

# Removing datetime column as index
gdf.reset_index(drop=False,
                inplace=True)


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



