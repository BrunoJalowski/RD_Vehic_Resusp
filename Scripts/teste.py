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
import rioxarray as rxr
import emission_factors as ef

#%%
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
#%%Plotar gdf
gdf.plot()

#%%Recorte em gdf menor com colunas importantes
gdf_cut = gdf.loc[ : , ['id','timestamp','length','flow','surface','road_category','geometry'] ]
gdf_cut

#%%Conversão timestamp to datetime
gdf_cut.loc[:,'datetime'] = gdf_cut.loc[:,'timestamp'].apply(datetime.fromtimestamp)

#%%Filtragem de flow=Nan
gdf_filtered = gdf_cut.dropna(axis=0)
gdf_filtered.plot()

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


#%%Add emissoes PM2.5 por trecho de via pavimentada
EF_paved = ef.emission_paved_roads(2.5, 1, 25)
EF_paved_corrected = ef.paved_rainfall_correction(EF_paved, 0, 365)
gdf_filtered.loc[gdf_filtered['surface']=='paved','emission'] = gdf_filtered.loc[gdf_filtered['surface']=='paved','flow'] * gdf_filtered.loc[gdf_filtered['surface']=='paved','length']/1000 * EF_paved 

