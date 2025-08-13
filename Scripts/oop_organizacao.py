#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Aug 13 17:46:16 2025

@author: brunojalowski
"""
import geopandas as gpd
from pathlib import Path
#%% Paths
project_path = Path('/home/brunojalowski/Documentos/RD_Vehic_Resusp/'
                    'dados_entrada')

flow_path = (project_path /
             'vehicle_count_daily-2025-07-09 00:00:00_to_2025-07-10 '
             '00:00:00_rev1.parquet')

#%%

class RoadDataset:
    def __init__(self, flow_path):
        self.dataframe = (gpd
                          .read_parquet(path=flow_path)
                          .astype({'osm_id': int,
                                   'vehicle_count': float,
                                   'average_daily_vehicle_count': float,
                                   'road_length': float,
                                   'vkt_per_hour': float,
                                   'surface': str,
                                   'avg_traffic_level': float})
                          .reset_index(drop=False)
                          )
        
    def classify_pavement(self):
        self.loc[(gdf['surface'] == 'asphalt') |
                (gdf['surface'] == 'paving_stones') |
                (gdf['surface'] == 'sett') |
                (gdf['surface'] == 'cobblestone') |
                (gdf['surface'] == 'metal') |
                (gdf['surface'] == 'concrete:plates'),
                'surface'] = 'paved'

        self.loc[(gdf['surface'] == 'compacted') |
                (gdf['surface'] == 'None') |
                (gdf['surface'] is None) |
                (gdf['surface'] == 'ground') |
                (gdf['surface'] == 'gravel') |
                (gdf['surface'] == 'dirt'), 'surface'] = 'unpaved'
    
    def assign_soil_moisture(self, soil_moisture_grid):
        
    
class Industries:
    pass
    


# %%
gdf = RoadDataset(flow_path)
