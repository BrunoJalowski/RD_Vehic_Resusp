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
import emission_factors

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
gdf_cut = gdf.loc[ : , ['id','timestamp','length','flow','road_category','geometry'] ]
gdf_cut

#%%Conversão timestamp to datetime
gdf_cut.loc[:,'datetime'] = gdf_cut.loc[:,'timestamp'].apply(datetime.fromtimestamp)

#%%Filtragem de flow=Nan
gdf_filtered = gdf_cut.dropna(axis=0)
gdf_filtered.plot()

#%%Arredondar flow para cima
gdf_filtered.loc[:,'flow'] = gdf_filtered.loc[:,'flow'].apply(math.ceil)

#%%Calculo de emissoes por via
EF = 0.062
gdf_filtered.loc[:,'emission'] = gdf_filtered.loc[:,'flow'] * gdf_filtered.loc[:,'length']/1000 * EF 

