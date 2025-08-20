#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Aug 19 13:48:15 2025

@author: brunojalowski
"""

import geopandas as gpd
from pathlib import Path
from long_2_utm_zone import long_2_utm_zone
from utm_zone_2_epsg import utm_zone_2_epsg
import pandas as pd

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

# %% ROAD TEMPLATE
roads = gdf.drop_duplicates(subset='osm_id').reset_index(drop=True)

# %% AIR MONITORING STATIONS
stations = gpd.read_file('/home/brunojalowski/Documentos/RD_Vehic_Resusp/'
                         'dados_entrada/Monitoramento_Qar_BR_teste.csv')

stations = gpd.GeoDataFrame(stations,
                            geometry=gpd.points_from_xy(stations.LONGITUDE,
                                                        stations.LATITUDE,
                                                        crs='EPSG:4326'))

stations.loc[:,'utm_zone'] = long_2_utm_zone(stations
                                               .geometry
                                               .centroid
                                               .x) 

# Atribuindo código EPSG SIRGAS 2000 projetado de acordo com a zona 
# UTM e a latitude
stations.loc[:,'EPSG'] = utm_zone_2_epsg(stations['utm_zone'],
                                           stations.geometry
                                           .centroid
                                           .x)

stations.drop(columns='utm_zone', inplace=True)


# %% SJOIN NEAREST
# Getting road closest to each station
joined = gpd.sjoin_nearest(stations,
                           roads,
                           how='inner')



# %% 
# Creating epsg dictionary
choices = {'{}'.format(q): q for q in stations['EPSG'].unique()}
roads_subsets = {}
stations_subsets = {}

# Creating sub dataframes
for epsg in choices.keys():
    
     # Creating sub dataframe and setting respective crs
     stations_subsets[epsg] = stations[stations['EPSG'] == epsg].to_crs(epsg)
     
     # Creating sub dataframe of roads for each EPSG
     """creates a subset with all roads that are the closest to a station 
     inside given epsg and converts it to that crs"""
     roads_subsets[epsg] = (
         roads[roads['osm_id'].isin(
             joined[joined['EPSG'] == epsg]['osm_id'].unique()
             )].to_crs(epsg))
     
     
     #
     stations_subsets[epsg] = gpd.sjoin_nearest(stations_subsets[epsg],
                                                roads_subsets[epsg],
                                                distance_col='distance')
     
     #stations_subsets[epsg] = stations_subsets[epsg].sort_values(by='average_daily_vehicle_count', ascending=False)
     #stations_subsets[epsg] = stations_subsets[epsg].drop_duplicates(subset='', keep="first")
     
     # Reprojecting geometry of each sub dataframe to WGS 84
     stations_subsets[epsg] = stations_subsets[epsg].to_crs(4326)
     
# Concatenating sub gdfs back to main gdf
stations = gpd.GeoDataFrame(pd.concat([stations_subsets[df]
                                       for df
                                       in stations_subsets]))

# Deactivates scientific notation
pd.set_option('display.float_format', '{:.2f}'.format)

# %%
