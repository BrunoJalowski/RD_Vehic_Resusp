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
from trafficdata.utils.geometries import split_lines_vectorized
import time

# %% PATH
project_path = Path('/home/brunojalowski/Documentos/RD_Vehic_Resusp/inputs')
# "C:\Users\bruno\Desktop\LCQAr\RD_Vehic_Resusp\dados_entrada"

industrial_path = project_path /'Industrias'

mining_path = industrial_path / 'MiningBR/BRASIL_FILTRADO.shp'

inventory_path = industrial_path / 'emission_total_light.csv'

landfills_path = (industrial_path / 'SINISA_RESIDUOS_Planilhas_2023/'
                  'SINISA_RESIDUOS_Informacoes_Formulario_Infraestrutura'
                  '_Destinacao_Final_2023.xlsx')

# %% INDUSTRIES FROM MMA INVENTORY
inventory_gdf = pd.read_csv(inventory_path)

# Creating gdf
inventory_gdf = gpd.GeoDataFrame(inventory_gdf,
                                  geometry=gpd.points_from_xy(inventory_gdf.Longitude,
                                                              inventory_gdf.Latitude,
                                                              crs='EPSG:4326'))

inventory_gdf = inventory_gdf[['SETOR','geometry']]

# %% Assigning silt loading values for each category
'''
array(['Refino de petróleo', 'Combustão externa - indústria',
       'Produção de clínquer e cimento',
       'Indústria Química - Fertilizantes fosfatados',
       'Indústria Química - Ácido sulfúrico',
       'Indústria Química - Negro de fumo',
       'Indústria Química - Látex SBR', 'Indústria Química - HIPS',
       'Indústria Química - Estireno', 'Indústria Química - EPS',
       'Indústria Química - Polipropileno',
       'Indústria Química - Nitrato de amônio',
       'Indústria Química - Ureia', 'Indústria Química - Oxirano',
       'Indústria Química - Sulfato de amônio',
       'Indústria Química - Borracha de EB',
       'Indústria Química - Propileno', 'Indústria Química - Eteno',
       'Indústria Química - PVC', 'Produção de ferro e aço',
       'Indústria de veículos automotores - revestimento de carros',
       'Produção de Celulose e Papel'], dtype=object)
'''

"""Dentre as atividades presentes, as unicas que se enquadram nas atividades
industriais com valores de silt loading padrão da AP42 são:
    - 'Produção de clínquer e cimento
    - 'Produção de ferro e aço'
    
"""

# Iron and Steel production
inventory_gdf.loc[inventory_gdf.SETOR
                  .isin(['Produção de ferro e aço']),
                  'silt_loading'] = 9.7

# Concrete batching
inventory_gdf.loc[inventory_gdf.SETOR
                  .isin(['Produção de clínquer e cimento']),
                  'silt_loading'] = 12

# Filtering industries that have no default silt loading 
inventory_gdf = inventory_gdf.loc[inventory_gdf.silt_loading.notna(),:]

inventory_gdf = inventory_gdf.drop(columns='SETOR')

# %% Getting UTM zone for each point

# Creating column with UTM zone for each point
inventory_gdf['EPSG'] = long_2_utm_zone(inventory_gdf.geometry.x)

# Creating column with EPSG code
inventory_gdf['EPSG'] = utm_zone_2_epsg(inventory_gdf['EPSG'],
                                        inventory_gdf.geometry.y)

# %% CREATING BUFFERS

# Creating epsg dictionary
choices = {'{}'.format(q): q for q in inventory_gdf['EPSG'].unique()}

# Creating sub dataframes and buffers
for epsg in choices.keys():
    
     # Creating sub dataframe and setting respective crs
     choices[epsg] = inventory_gdf[inventory_gdf['EPSG'] == epsg].to_crs(epsg)
     
     # Creating buffers in km and converting to WGS 84
     choices[epsg]['buffer_ind'] = choices[epsg].buffer(500).to_crs(4326)
     choices[epsg]['buffer_amort'] = choices[epsg].buffer(600).to_crs(4326)
     
     # Reprojecting geometry of each sub dataframe to WGS 84
     choices[epsg] = choices[epsg].to_crs(4326)
     
# Concatenating sub gds back to main gdf
inventory_gdf = gpd.GeoDataFrame(pd.concat([choices[df] for df in choices])) 

del choices

# %% Plotting industrial sites
# =============================================================================
# fig, ax = plt.subplots(figsize=(10,10))
# industrial_gdf['buffer_2km'].plot(ax=ax, facecolor='none')
# industrial_gdf['buffer_5km'].plot(ax=ax, facecolor='none')
# 
# 
# =============================================================================



# %% LANDFILL SITES =========================================================

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
                               ['GTR3203*','GTR3204*']]
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
landfill_points = landfill_points.rename(columns={'GTR3203*':'Latitude',
                                                  'GTR3204*':'Longitude'})

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

landfill_gdf.drop(columns=['utm_zone','Latitude','Longitude'], inplace=True)

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


# Assigning silt loading value for the entire landfill gdf
landfill_gdf['silt_loading'] = 7.4



# %% MINING SITES ============================================================

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

# Selecting important columns
mining_gdf = mining_gdf.loc[:,['geometry', 'EPSG','buffer_ind',
                               'buffer_amort', 'silt_loading']]











# %% CONCATENATING LANDFILL AND OTHER INDUSTRIAL ACTIVITIES
industrial_gdf = pd.concat([inventory_gdf,landfill_gdf, mining_gdf]).reset_index(drop=True)

del landfill_gdf, mining_gdf

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
buffer_ind.to_parquet(industrial_path /'buffer_ind.parquet')
buffer_amort.to_parquet(industrial_path /'buffer_amort.parquet')


industrial_gdf.to_parquet(industrial_path /
                          'industrial_sites_20251024.parquet')


