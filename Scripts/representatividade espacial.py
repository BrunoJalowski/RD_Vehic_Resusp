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
from Industrial_Sites import industrial_gdf
# Deactivates scientific notation
pd.set_option('display.float_format', '{:.2f}'.format)

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
# Get roads for a single instant of time (drop temporal duplicates)
roads = gdf.drop_duplicates(subset='osm_id').reset_index(drop=True)

# Filter all roads with adt lesser than 10k
roads = roads[roads['average_daily_vehicle_count'] > 10000]

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
# =============================================================================
# 
# # Getting industry closest to each station
# station_join_industries = gpd.sjoin_nearest(stations,
#                                             industrial_gdf,
#                                             how='left')
# =============================================================================


# %% 
# Creating epsg dictionary
choices = {'{}'.format(q): q for q in stations['EPSG'].unique()}

# Creating dictionaries of subsets for each EPSG 
roads_subsets = {}
stations_subsets = {}
industries_subsets = {}

# List of average daily vehicle count (value * 1000)
adt_list = [10, 15, 20, 30, 40, 50, 60, 70, 80, 110, 10000000]

# Creating sub dataframes for each EPSG code
for epsg in choices.keys():
    
     # Creating stations sub dataframe and setting respective crs
     stations_subsets[epsg] = stations[stations['EPSG'] == epsg].to_crs(epsg)

     # Creating sub dataframe of roads for each EPSG
     roads_subsets[epsg] = roads.to_crs(epsg)


     # Creating sub dataframe of industries for each EPSG
     """creates a subset with all industries that are the closest to a station 
     inside given epsg and converts it to that crs"""
     industries_subsets[epsg] = industrial_gdf.to_crs(epsg)
     
     # Calculates distance from each station to closest road amongst all roads
     stations_subsets[epsg] = (
         gpd.sjoin_nearest(stations_subsets[epsg],
                           roads_subsets[epsg][['osm_id',
                                                'average_daily_vehicle_count',
                                                'geometry']],
                           distance_col="distance_closest_road"))
     
     # Dropping right index from sjoin
     stations_subsets[epsg].drop(columns='index_right', inplace=True)
     
     # Calculating distance between the closest road, for each road class
     for idx, adt in enumerate(adt_list[0:-1]):
         stations_subsets[epsg] = (
            gpd.sjoin_nearest(stations_subsets[epsg],
                              roads_subsets[epsg]
                              .loc[(roads_subsets[epsg]['average_daily_vehicle_count'] >= adt * 1000) &
                                   (roads_subsets[epsg]['average_daily_vehicle_count'] < adt_list[idx + 1] * 1000),
                                   ['osm_id', 'average_daily_vehicle_count', 'geometry']],
                              how='left',
                              lsuffix=('{}k'.format(adt_list[idx - 1])
                                                   if idx > 0
                                                   else 'closest_road'),
                              rsuffix='{}k'.format(adt),
                              distance_col='distance_{}k'.format(adt))
            )

         # Dropping right index from sjoin
         stations_subsets[epsg].drop(columns='index_{}k'.format(adt), inplace=True)
    
     # Calculates distance from each station to closest industry
     stations_subsets[epsg] = (
         gpd.sjoin_nearest(stations_subsets[epsg],
                           industries_subsets[epsg][['Razão Social',
                                                     'activity_id',
                                                     'geometry']],
                           distance_col="distance_to_industry"))
     
     # Dropping right index from sjoin
     stations_subsets[epsg].drop(columns='index_right', inplace=True)
     
     # Reprojecting geometry of each sub dataframe to WGS 84
     stations_subsets[epsg] = stations_subsets[epsg].to_crs(4326)
     
     
# Concatenating sub gdfs back to main gdf
distance_from_roads = gpd.GeoDataFrame(pd.concat([stations_subsets[df]
                                                  for df
                                                  in stations_subsets]
                                                 )
                                       )

#%% Representativeness Classification



distance_from_roads['rep_scale'] = distance_from_roads()


#%% Representativeness buffer 
"""microscale: < 100 m
   mesoscale: 100 m < x < 500 m
   neighbourhood scale: 500 m < x < 4000 m
   urban scale: 4000 m < x < 50000 m
""" 


#%%
# =============================================================================
# # Verifique qual é a coluna que identifica unicamente as estações, substitua se necessário
# counts = distance_from_roads['ID_MMA_COMPLETO'].value_counts()
# duplicated_stations = counts[counts > 1]
# print(f"Número de estações com duplicatas: {len(duplicated_stations)}")
# print(duplicated_stations.head())
# 
# gdf_duplicated = distance_from_roads[distance_from_roads['ID_MMA_COMPLETO'].isin(duplicated_stations.index)]
# 
# # Exemplo com uma estação duplicada
# example_id = duplicated_stations.index[0]
# gdf_duplicated[gdf_duplicated['ID_MMA_COMPLETO'] == example_id][
#     ['ID_MMA_COMPLETO', 'distance_10k', 'osm_id_10k']
# ]
# 
# gdf = gdf.sort_values(by='osm_id_10k')  # ou outra coluna
# gdf = gdf.drop_duplicates(subset='ID_MMA_COMPLETO', keep='first')
# =============================================================================

