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
import rioxarray as rxr
import emission_factors as ef
import matplotlib.pyplot as plt
import netcdf4_conversions_v2 as conv
import numpy as np
import rasterio
#%%Dados de velocidade do Tomtom combinado com dados de fluxo 
gdf = gpd.read_file('/home/brunojalowski/Documentos/RD_Vehic_Resusp/dados_entrada/4.speed_equation/2025-01-22_01_merged_merged_speed.gpkg')
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

#%%Recorte em gdf menor com colunas importantes
gdf_cut = gdf.loc[ : , ['id','timestamp','traffic_level',
                        'length','flow','surface','road_category','geometry'] ]

#%%Conversão timestamp to datetime
gdf_cut.loc[:,'datetime'] = gdf_cut.loc[:,'timestamp'].apply(datetime.fromtimestamp)

#%%Filtragem de flow=Nan
gdf_filtered = gdf_cut.dropna(axis=0)

del gdf, gdf_cut
#%%Arredondar flow para cima
gdf_filtered.loc[:,'flow'] = gdf_filtered.loc[:,'flow'].apply(math.ceil)

#%%Reclassificação superfície das vias
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



#%% Determinando Silt loading padrão de acordo com o ADT das vias
""" Silt loading segundo valores de Average Daily Traffic (ADT) da AP-42 "Paved Roads":
            ADT <   500 --> 0.6
    500   < ADT >  5000 --> 0.2
    5000  < ADT > 10000 --> 0.06
    10000 < ADT         --> 0.03
    """



gdf_filtered.loc[:,'silt_loading'] = gdf_filtered.loc[:,'flow']



