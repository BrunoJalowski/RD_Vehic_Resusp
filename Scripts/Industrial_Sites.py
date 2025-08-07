#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May 12 11:18:59 2025

@author: brunojalowski
"""

import pandas as pd
import numpy as np
from pathlib import Path
import glob
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.colors as mcolors
import geopandas as gpd
from long_2_utm_zone import long_2_utm_zone
from utm_zone_2_epsg import utm_zone_2_epsg
from road_preprocess import gdf
from trafficdata.utils.geometries import split_lines_vectorized
import time

# %% PATH
project_path = Path('/home/brunojalowski/Documentos/RD_Vehic_Resusp/dados_entrada')
# "C:\Users\bruno\Desktop\LCQAr\RD_Vehic_Resusp\dados_entrada"
industrial_path = project_path /'Industrias'
mining_path = industrial_path / 'MiningBR/BRASIL_FILTRADO.shp'
cnpj_path = industrial_path / 'PessoasJuridicas'
landfills_path = (industrial_path / 'SINISA_RESIDUOS_Planilhas_2023/'
                  'SINISA_RESIDUOS_Informacoes_Formulario_Infraestrutura'
                  '_Destinacao_Final_2023.xlsx')

# %% Fusão de todas as planilhas de Pessoas Juridicas
files = glob.glob(str(cnpj_path / '*.csv'))
cnpj_df = pd.read_csv(files[0], sep='\t', skiprows=2)

for file in files[1:]:
    opened = pd.read_csv(file, sep='\t', skiprows=2)
    cnpj_df = pd.merge(cnpj_df, opened, how='outer')


del opened, files, file

# %% Replacing commas with dots in the coordinates
cnpj_df.Latitude = (cnpj_df['Latitude']
                    .str.replace(',', '.', regex=False)
                    .astype(float))
cnpj_df.Longitude = (cnpj_df['Longitude']
                     .str.replace(',', '.', regex=False)
                     .astype(float))

# %% Filtrando

"""Filtrando:
    - Atividade industriais presentes na tabela de Default Silt Loading da
    AP42:
        3.1: Fabricação de aço e de produtos siderúrgicos
        3.2: Produção de fundidos de ferro e aço, forjados, arames, 
        relaminados com ou sem tratamento de superfície, inclusive 
        galvanoplastia
        3.11: Têmpera e cementação de aço, ecozimento de arames e tratamento 
        de superfície
        14.1: Produção de Cimento
        14.2: Produção de Concreto
        16.1: Beneficiamento, moagem, torrefação e fabricação de produtos
        alimentares
    - Em situação cadastral ativa
    """
cnpj_df = cnpj_df.loc[(
    (cnpj_df['Código da categoria'] == 3) &
    (cnpj_df['Situação cadastral'] == 'Ativa') &
    (cnpj_df['Código da atividade'].isin([1, 2, 11]))
    ) |
    ((cnpj_df['Código da categoria'] == 14) &
     (cnpj_df['Situação cadastral'] == 'Ativa') &
     (cnpj_df['Código da atividade'].isin([1, 2]))
    ) |
    ((cnpj_df['Código da categoria'] == 16) &
     (cnpj_df['Situação cadastral'] == 'Ativa') &
     (cnpj_df['Código da atividade'] == 1)
    ), :]

# %% Assigning silt loading values for each category

# Iron and Steel production
cnpj_df.loc[
    (cnpj_df['Código da categoria'] == 3) &
    (cnpj_df['Código da atividade'].isin([1, 2, 11])),
    'silt_loading'] = 9.7

# Asphalt batching
cnpj_df.loc[
    (cnpj_df['Código da categoria'] == 14) &
    (cnpj_df['Código da atividade'] == 1),
    'silt_loading'] = 120

# Concrete batching
cnpj_df.loc[
    (cnpj_df['Código da categoria'] == 14) &
    (cnpj_df['Código da atividade'] == 2),
    'silt_loading'] = 12

# Corn wet mills (applyed to all grains)
cnpj_df.loc[
    (cnpj_df['Código da categoria'] == 16) &
    (cnpj_df['Código da atividade'] == 1),
    'silt_loading'] = 1.1

# %% Creating geometry column
cnpj_gdf = gpd.GeoDataFrame(cnpj_df,
                            geometry=gpd.points_from_xy(cnpj_df.Longitude,
                                                        cnpj_df.Latitude,
                                                        crs='EPSG:4326'))
del cnpj_df


# %% Getting UTM zone for each point

# Creating column with UTM zone for each point
cnpj_gdf['EPSG'] = long_2_utm_zone(cnpj_gdf['Longitude'])

# Removing points outside of Brazil
cnpj_gdf = cnpj_gdf.dropna()
cnpj_gdf = cnpj_gdf.loc[(cnpj_gdf['Longitude'] != 0) |
                         (cnpj_gdf['Latitude'] != 0)]

# Creating column with EPSG code
cnpj_gdf['EPSG'] = utm_zone_2_epsg(cnpj_gdf['EPSG'],
                                   cnpj_gdf['Latitude'])

# %% CREATING BUFFERS

# Creating epsg dictionary
choices = {'{}'.format(q): q for q in cnpj_gdf['EPSG'].unique()}

# Creating sub dataframes and buffers
for epsg in choices.keys():
    
     # Creating sub dataframe and setting respective crs
     choices[epsg] = cnpj_gdf[cnpj_gdf['EPSG'] == epsg].to_crs(epsg)
     
     # Creating buffers in km and converting to WGS 84
     choices[epsg]['buffer_ind'] = choices[epsg].buffer(500).to_crs(4326)
     choices[epsg]['buffer_amort'] = choices[epsg].buffer(600).to_crs(4326)
     
     # Reprojecting geometry of each sub dataframe to WGS 84
     choices[epsg] = choices[epsg].to_crs(4326)
     
# Concatenating sub gds back to main gdf
industrial_gdf = gpd.GeoDataFrame(pd.concat([choices[df] for df in choices])) 

del cnpj_gdf, choices

# %% Plotting industrial sites
# =============================================================================
# fig, ax = plt.subplots(figsize=(10,10))
# industrial_gdf['buffer_2km'].plot(ax=ax, facecolor='none')
# industrial_gdf['buffer_5km'].plot(ax=ax, facecolor='none')
# 
# 
# =============================================================================




























# %% LANDFILL SITES

# Reading list of brazilian landfills from SINISA
landfill = pd.read_excel(landfills_path, engine='openpyxl', skiprows=10)

#%% COLUMN CODES AND NAMES
dicts = {}
for column in landfill.columns:
    dicts[landfill.loc[1,column]] = column
"""
{'Sim/Não': 'RESPONDEU AO MÓDULO DE MANEJO DE RESÍDUOS SÓLIDOS 2023 ',
 'Cod_IBGE': 'CÓDIGO DO IBGE',
 'Nom_Mun': 'MUNICÍPIO SEDE UNIDADE',
 'UF': 'UF',
 'Nom_Região': 'MACRORREGIÃO',
 'Capital': 'CAPITAL',
 'CAD1000 ': 'CNPJ',
 'CAD1001 ': ' SECRETARIA OU SETOR RESPONSÁVEL',
 'CAD1002': 'NATUREZA JURÍDICA',
 'DFE0001': 'POPULAÇÃO TOTAL',
 'DFE0002': 'POPULAÇÃO URBANA',
 'DFE0003': 'POPULAÇÃO RURAL',
 'OGM4006': 'Quantidade de domicílios totais existente no município',
 'OGM4004': 'Quantidade de domicílios urbanos existente no município',
 'OGM4005': 'Quantidade de domicílios rurais existente no município',
 'OGM0005': 'Área (Km²)',
 'GTR3200': 'Código',
 'GTR3201*': 'Tipo de unidade de disposição final',
 'GTR3202*': 'Nome da unidade de disposição final',
 'GTR3203*': 'Localização geográfica da unidade de disposição final - Latitude',
 'GTR3204*': 'Localização geográfica da unidade de disposição final - Longitude',
 'GTR3205*': 'A unidade de disposição final esteve em operação no ano de referência?',
 'GTR3206*': 'Situação da unidade de disposição final inoperante',
 'GTR3207*': 'Proprietário da unidade de disposição final\xa0',
 'GTR3208*': 'Ano de início da operação da unidade de disposição final ',
 'GTR3209*': 'Executor do serviço de disposição final ',
 'GTR3210*': 'Tipo de licença ambiental da unidade de disposição final',
 'GTR3210A*': 'Outro nome (especificar)',
 'GTR3220': 'Quantidade de resíduos sólidos de lodo desidratado (torta) de serviços de saneamento básico',
 'GTR3221': 'Quantidade de resíduos sólidos da coleta de grandes geradores ou geradores específicos',
 'GTR3223': 'Quantidade total recebida na unidade de disposição final',
 'GTR3224\xa0': 'Fatores ambientais e sociais constantes no local de disposição final',
 'GTR3225\xa0': 'Equipamentos utilizados na unidade de disposição final',
 'GTR3226*': 'Controle de pesagem dos resíduos na unidade de disposição final',
 'GTR3227*': 'Infraestrutura existente na área de disposição final',
 'GTR3230\xa0': ' Capacidade instalada máxima da unidade de disposição final',
 'GTR3231\xa0': 'Capacidade já utilizada da unidade de disposição final até o fim do ano de referência',
 'GTR3232*': 'Sistemas de proteção ambiental em operação na unidade de disposição final',
 'GTR3233*': 'Frequência do recobrimento dos resíduos sólidos na unidade de disposição final ',
 'GTR3234*': 'Caracterização do sistema de drenagem e capatação dos gases de forma ativa (sucção forçada)',
 'GTR3235*': 'Quantidade de biometano gerada',
 'GTR3236*': 'Quantidade de energia elétrica gerada'}
"""

del column, dicts

#%% Opening dataframe with codes as column names
landfill = pd.read_excel(landfills_path, engine='openpyxl', skiprows=12 )
    
#%% Filtering important columns
landfill_points = landfill.loc[(~pd.isna(landfill['GTR3203*']) &
                               ~pd.isna(landfill['GTR3204*'])),
                               ['CAD1000 ','GTR3202*','GTR3203*','GTR3204*']]
del landfill

# Formatting coordinates
landfill_points.loc[:, 'GTR3203*'] = (landfill_points
                                      .loc[:, 'GTR3203*']
                                      .str.split()
                                      .str[-1])

landfill_points.loc[:, 'GTR3204*'] = (landfill_points
                                      .loc[:, 'GTR3204*']
                                      .str.split()
                                      .str[-1])

# Turning coordinates to float
landfill_points.loc[:, 'GTR3203*'] = (landfill_points
                                      .loc[:, 'GTR3203*']
                                      .astype(float))

landfill_points.loc[:, 'GTR3204*'] = (landfill_points
                                      .loc[:, 'GTR3204*']
                                      .astype(float))

# Renaming columns
landfill_points = landfill_points.rename(columns={'CAD1000 ':'CNPJ',
                                                  'GTR3203*':'Latitude',
                                                  'GTR3204*':'Longitude',
                                                  'GTR3202*':'Nome'})

#%%
# Creating geodataframe from lon and lat columns
landfill_gdf = (
    gpd.GeoDataFrame(landfill_points,
                     geometry = gpd.points_from_xy(landfill_points.Longitude,
                                                   landfill_points.Latitude),
                     crs="EPSG:4326")
    )
# Resetting index
landfill_gdf = landfill_gdf.reset_index(drop=True)

del landfill_points 

# %% Creating column with epsg code for each landfill

# Getting utm zone using the longitude
landfill_gdf.loc[:,'utm_zone'] = long_2_utm_zone(landfill_gdf['Longitude']) 

# Assigning EPSG SIRGAS 2000 code according to UTM zone and latitude
landfill_gdf.loc[:,'EPSG'] = utm_zone_2_epsg(landfill_gdf['utm_zone'],
                                             landfill_gdf['Latitude'])

landfill_gdf.drop(columns='utm_zone', inplace=True)

# %% CREATING BUFFERS
# Creating epsg dictionary
choices = {'{}'.format(q): q for q in landfill_gdf['EPSG'].unique()}

# Creating sub dataframes and buffers
for epsg in choices.keys():
    
     # Creating sub dataframe and setting respective crs
     choices[epsg] = landfill_gdf[landfill_gdf['EPSG'] == epsg].to_crs(epsg)
     
     # Creating buffers in km and converting to WGS 84
     choices[epsg]['buffer_ind'] = choices[epsg].buffer(500).to_crs(4326)
     choices[epsg]['buffer_amort'] = choices[epsg].buffer(600).to_crs(4326)
     
     # Reprojecting geometry of each sub dataframe to WGS 84
     choices[epsg] = choices[epsg].to_crs(4326)


# Concatenating sub gds back to main gdf
landfill_gdf = gpd.GeoDataFrame(pd.concat([choices[df] for df in choices])) 

del epsg, choices
# =============================================================================
# fig, ax = plt.subplots(figsize=(10,10))
# landfill_gdf['buffer_2km'].plot(ax=ax, facecolor='none')
# landfill_gdf['buffer_5km'].plot(ax=ax, facecolor='none')roads
# =============================================================================

# %% Assigning silt loading value for the entire landfill gdf
landfill_gdf['silt_loading'] = 7.4







# %% MINING SITES

# Opening mining sites geodataframe
mining_gdf = gpd.read_file(mining_path, engine='fiona')

# %% Creating column with EPSG code

# Getting UTM zone from Longitude
mining_gdf.loc[:,'utm_zone'] = long_2_utm_zone(mining_gdf
                                               .geometry
                                               .centroid
                                               .x) 

# Atribuindo código EPSG SIRGAS 2000 projetado de acordo com a zona 
# UTM e a latitude
mining_gdf.loc[:,'EPSG'] = utm_zone_2_epsg(mining_gdf['utm_zone'],
                                           mining_gdf.geometry
                                           .centroid
                                           .x)

mining_gdf.drop(columns='utm_zone', inplace=True)

# %% CREATING BUFFERS
# Creating epsg dictionary
choices = {'{}'.format(q): q for q in mining_gdf['EPSG'].unique()}

# Creating sub dataframes and buffers
s = time.time()
for epsg in choices.keys():
    
     # Creating sub dataframe and setting respective crs
     choices[epsg] = mining_gdf[mining_gdf['EPSG'] == epsg].to_crs(epsg)
     
     # Creating buffers in km and converting to WGS 84
     choices[epsg]['buffer_ind'] = choices[epsg].buffer(500).to_crs(4326)
     choices[epsg]['buffer_amort'] = choices[epsg].buffer(600).to_crs(4326)
     
     # Reprojecting geometry of each sub dataframe to WGS 84
     choices[epsg] = choices[epsg].to_crs(4326)

mining_time = time.time() - s

# Concatenating sub gds back to main gdf
mining_gdf = gpd.GeoDataFrame(pd.concat([choices[df] for df in choices])) 

del epsg, choices, s

#%% Assigning silt loading values to mining sites following the Quarry 
# classification in AP42

mining_gdf['silt_loading'] = 8.2











# %% CONCATENATING LANDFILL AND OTHER INDUSTRIAL ACTIVITIES
industrial_gdf = pd.concat([industrial_gdf,landfill_gdf, mining_gdf]).reset_index()

del landfill_gdf, mining_gdf

industrial_gdf.loc[~pd.isna(industrial_gdf['Nome']),
                   'Razão Social'] = industrial_gdf['Nome']
industrial_gdf.loc[~pd.isna(industrial_gdf['NOME']),
                   'Razão Social'] = industrial_gdf['NOME']

industrial_gdf.drop(columns=['Nome', 'NOME'], inplace=True)

# %% Creating identifier column for each industrial site
industrial_gdf['activity_id'] = industrial_gdf.index

#%% SAVING BUFFERS TO GEOPACKAGE
buffer_ind = gpd.GeoDataFrame(data=industrial_gdf[['activity_id','silt_loading']],
                              geometry=industrial_gdf['buffer_ind'])

buffer_amort = gpd.GeoDataFrame(data=industrial_gdf[['activity_id','silt_loading']],
                                geometry=industrial_gdf['buffer_amort'])

buffer_amort['silt_loading'] = (buffer_amort['silt_loading'] + 0.6) / 2

"""Transition values are an average between industrial and the upper limit of 
AP-42 default silt loading, 0.6 g/m²"""

# Saving to gpkg files
buffer_ind.to_file(filename=industrial_path /'buffer_ind.gpkg',
                   driver='GPKG')
buffer_amort.to_file(filename=industrial_path /'buffer_amort.gpkg',
                     driver='GPKG')

del industrial_gdf
# %% Getting all roads for a single timestep
roads = gdf.loc[:,['osm_id','geometry']]
roads = roads.drop_duplicates(subset='osm_id').reset_index(drop=True)


# %% Segmenting all roads with buffers
buffer_ind_bound = gpd.GeoDataFrame(data=buffer_ind['silt_loading'],
                              geometry=buffer_ind.boundary)
buffer_amort_bound = gpd.GeoDataFrame(data=buffer_amort['silt_loading'],
                                geometry=buffer_amort.boundary)

# Splitting roads by wider buffers
roads_template = split_lines_vectorized(roads, buffer_amort_bound.explode())

# Splitting roads by more restrict buffers
roads_template = split_lines_vectorized(roads_template, buffer_ind_bound.explode())

"""The roads_template variable will be used as the default layer for roads
from this point on. All new road information will be assigned to this
GeoDataFrame via osm_id"""


#%% Creating unique id for every road segment
roads_template['segment_id'] = [f'segment_{i}' for i in range(len(roads_template))]

#%% INTERSECTING INTERNAL BUFFERS

# filtering with sjoin for intersection
candidates_ind = gpd.sjoin(buffer_ind,
                           roads_template,
                           how='inner',
                           predicate='intersects')

geoms_for_intersect_01 = (buffer_ind
                          .loc[candidates_ind.index]
                          .reset_index(drop=False))

geoms_for_intersect_02 = (roads_template
                          .loc[candidates_ind['index_right']]
                          .reset_index(drop=False))
del candidates_ind

# Getting all roads that intersects buffers 
intersected_ind = geoms_for_intersect_01.intersection(geoms_for_intersect_02)


# Filtering points from result
roads_ind = intersected_ind.loc[intersected_ind
                                .geometry
                                .geom_type == 'LineString']

roads_ind = geoms_for_intersect_02.loc[roads_ind.index]

roads_ind['silt_loading'] = (geoms_for_intersect_01['silt_loading']
                             .loc[intersected_ind.index])

roads_ind.geometry = intersected_ind.loc[intersected_ind
                                         .geometry
                                         .geom_type == 'LineString'].geometry

del intersected_ind
#%% Checking intersections

# =============================================================================
# minx, miny, maxx, maxy = gdf.total_bounds
# fig, ax = plt.subplots(2)
# 
# # Intersected segments
# ax[0].set_xlim(minx-0.01, maxx+0.01)
# ax[0].set_ylim(miny-0.01, maxy+0.01)
# 
# roads_ind.plot(ax=ax[0], color='C0')
# buffer_ind.plot(ax=ax[0],
#                 facecolor='none')
# 
# # All roads
# ax[1].set_xlim(minx-0.01, maxx+0.01)
# ax[1].set_ylim(miny-0.01, maxy+0.01)
# roads.plot(ax=ax[1])
# buffer_ind.plot(ax=ax[1],
#                 facecolor='none')
# =============================================================================

# %% INTERSECTING EXTERNAL BUFFERS

# filtering with sjoin for intersection
candidates_amort = gpd.sjoin(buffer_amort,
                             roads_template,
                             how='inner',
                             predicate='intersects')

geoms_for_intersect_01 = (buffer_amort
                          .loc[candidates_amort.index]
                          .reset_index(drop=False))

geoms_for_intersect_02 = (roads_template
                          .loc[candidates_amort['index_right']]
                          .reset_index(drop=False))
del candidates_amort

# Getting all roads that intersect with buffers 
intersected_amort = geoms_for_intersect_01.intersection(geoms_for_intersect_02)

# Filtering points from result
roads_amort = intersected_amort.loc[intersected_amort
                                    .geometry
                                    .geom_type == 'LineString']

roads_amort = geoms_for_intersect_02.loc[roads_amort.index]
roads_amort['silt_loading'] = (geoms_for_intersect_01['silt_loading']
                               .loc[intersected_amort.index])

roads_amort.geometry = intersected_amort.loc[intersected_amort
                                             .geometry
                                             .geom_type == 'LineString'].geometry


del intersected_amort, geoms_for_intersect_01, geoms_for_intersect_02

#%% Checking intersections

# =============================================================================
# minx, miny, maxx, maxy = gdf.total_bounds
# fig, ax = plt.subplots(2)
# 
# # Intersected segments
# ax[0].set_xlim(minx-0.01, maxx+0.01)
# ax[0].set_ylim(miny-0.01, maxy+0.01)
# 
# roads_amort.plot(ax=ax[0], color='C0')
# buffer_amort.plot(ax=ax[0],
#                 facecolor='none')
# 
# # All roads
# ax[1].set_xlim(minx-0.01, maxx+0.01)
# ax[1].set_ylim(miny-0.01, maxy+0.01)
# roads.plot(ax=ax[1])
# buffer_amort.plot(ax=ax[1],
#                   facecolor='none')
# =============================================================================


# %% Concatenating intersected gdfs for final silt loading values 
"""For each segment, independing if it's from a ind or amort buffer, the
final silt_loading value will be the highest one that intercepts that
segment."""

# Concatenating 
intersected_roads = pd.concat([roads_ind, roads_amort], axis=0)

del roads_amort, roads_ind

# Grouping silt_loading values by segment_id
silt_loading_roads = (intersected_roads
                      .groupby(['segment_id'])['silt_loading']
                      .max())

# Assigning chosen values to road_segments
roads_template['silt_loading'] = (
    roads_template['segment_id']
    .map(silt_loading_roads)
)

del silt_loading_roads
#%% Plotting
# =============================================================================
# minx, miny, maxx, maxy = gdf.total_bounds
# 
# import os
# 
# # Creating road color list
# colors = [os.urandom(6).hex() for i in range(len(roads_template))]
# roads_template['colors'] = colors
# 
# # All roads
# fig, ax = plt.subplots()
# ax.set_xlim(minx-0.01, maxx+0.01)
# ax.set_ylim(miny-0.01, maxy+0.01)
# roads_template.plot(ax=ax, column='colors')
# buffer_amort_bound.plot(ax=ax)
# buffer_ind_bound.plot(ax=ax)
# 
# =============================================================================

del buffer_amort, buffer_amort_bound, buffer_ind, buffer_ind_bound
