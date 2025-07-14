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
import geopandas as gpd
import math
from long_2_utm_zone import long_2_utm_zone
from utm_zone_2_epsg import utm_zone_2_epsg
import regex as re
import fiona

# %% PATH
project_path = Path(r"C:\Users\bruno\Desktop\LCQAr\RD_Vehic_Resusp\dados_entrada")
industrial_path = project_path /'Industrias'
mining_path = industrial_path / 'MiningBR/BRASIL_FILTRADO.shp'
cnpj_path = industrial_path / 'PessoasJuridicas'
landfills_path = (industrial_path / 'SINISA_RESIDUOS_Planilhas_2023/'
                  'SINISA_RESIDUOS_Informacoes_Formulario_Infraestrutura'
                  '_Destinacao_Final_2023.xlsx')

# %% Fusão de todas as planilhas de Pessoas Juridicas
files = glob.glob(str(cnpj_path / '*.csv'))
main_df = pd.read_csv(files[0], sep='\t', skiprows=2)

for file in files[1:]:
    opened = pd.read_csv(file, sep='\t', skiprows=2)
    main_df = pd.merge(main_df, opened, how='outer')


del opened, files, file

# %% Replacing commas with dots in the coordinates
main_df.Latitude = (main_df['Latitude']
                    .str.replace(',', '.', regex=False)
                    .astype(float))
main_df.Longitude = (main_df['Longitude']
                     .str.replace(',', '.', regex=False)
                     .astype(float))

# %% Filtrando

"""Filtrando:
    - categorias industriais (1-16)
    - em situação cadastral ativa
    """
main_df = main_df.loc[(main_df['Código da categoria'] < 17) &
                      (main_df['Situação cadastral'] == 'Ativa'), :]

# %% Creating geometry column
main_gdf = gpd.GeoDataFrame(main_df,
                            geometry=gpd.points_from_xy(main_df.Longitude,
                                                        main_df.Latitude,
                                                        crs='EPSG:4326'))
del main_df


# %% Getting UTM zone for each point

# Creating column with UTM zone for each point
main_gdf['EPSG'] = long_2_utm_zone(main_gdf['Longitude'])

# Removing points outside of Brazil
main_gdf = main_gdf.dropna()
main_gdf = main_gdf.loc[(main_gdf['Longitude'] != 0) |
                         (main_gdf['Latitude'] != 0)]

# Creating column with EPSG code
main_gdf['EPSG'] = utm_zone_2_epsg(main_gdf['EPSG'],
                                   main_gdf['Latitude'])

# %% CREATING BUFFERS

# Creating epsg dictionary
choices = {'{}'.format(q): q for q in main_gdf['EPSG'].unique()}

# Creating sub dataframes and buffers
for epsg in choices.keys():
    
     # Creating sub dataframe and setting respective crs
     choices[epsg] = main_gdf[main_gdf['EPSG'] == epsg].to_crs(epsg)
     
     # Creating buffers in km and converting to WGS 84
     choices[epsg]['buffer_2km'] = choices[epsg].buffer(2000).to_crs(4326)
     choices[epsg]['buffer_5km'] = choices[epsg].buffer(5000).to_crs(4326)
     
     # Reprojecting geometry of each sub dataframe to WGS 84
     choices[epsg] = choices[epsg].to_crs(4326)
     
# Concatenating sub gds back to main gdf
industrial_gdf = gpd.GeoDataFrame(pd.concat([choices[df] for df in choices])) 

del main_gdf, choices

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
    
#%% Filtering importante columns

landfill_points = landfill.loc[(~pd.isna(landfill['GTR3203*']) &
                               ~pd.isna(landfill['GTR3204*'])),
                               ['CAD1000 ','GTR3202*','GTR3203*','GTR3204*']]
del landfill

# Limpando os dados de coordenadas
landfill_points.loc[:, 'GTR3203*'] = (landfill_points
                                      .loc[:, 'GTR3203*']
                                      .str.split()
                                      .str[-1])

landfill_points.loc[:, 'GTR3204*'] = (landfill_points
                                      .loc[:, 'GTR3204*']
                                      .str.split()
                                      .str[-1])

# Transformando em float
landfill_points.loc[:, 'GTR3203*'] = (landfill_points
                                      .loc[:, 'GTR3203*']
                                      .astype(float))

landfill_points.loc[:, 'GTR3204*'] = (landfill_points
                                      .loc[:, 'GTR3204*']
                                      .astype(float))

# Renomeando os códigos para os nomes mais sucintos
landfill_points = landfill_points.rename(columns={'CAD1000 ':'CNPJ',
                                                  'GTR3203*':'Latitude',
                                                  'GTR3204*':'Longitude',
                                                  'GTR3202*':'Nome'})

#%%
# Criando gdf de pontos por meio das coordenadas
landfill_gdf = (
    gpd.GeoDataFrame(landfill_points,
                     geometry = gpd.points_from_xy(landfill_points.Longitude,
                                                   landfill_points.Latitude),
                     crs="EPSG:4326")
    )
# Resetando indice
landfill_gdf = landfill_gdf.reset_index(drop=True)

# %% Criando coluna do Código EPSG 

# Pegando zona utm a partir da longitude
landfill_gdf.loc[:,'utm_zone'] = long_2_utm_zone(landfill_gdf['Longitude']) 

# Atribuindo código EPSG SIRGAS 2000 projetado de acordo com a zona 
# UTM e a latitude
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
     choices[epsg]['buffer_2km'] = choices[epsg].buffer(2000).to_crs(4326)
     choices[epsg]['buffer_5km'] = choices[epsg].buffer(5000).to_crs(4326)
     
     # Reprojecting geometry of each sub dataframe to WGS 84
     choices[epsg] = choices[epsg].to_crs(4326)


# Concatenating sub gds back to main gdf
landfill_gdf = gpd.GeoDataFrame(pd.concat([choices[df] for df in choices])) 

del epsg, choices
# =============================================================================
# fig, ax = plt.subplots(figsize=(10,10))
# landfill_gdf['buffer_2km'].plot(ax=ax, facecolor='none')
# landfill_gdf['buffer_5km'].plot(ax=ax, facecolor='none')
# =============================================================================





# %% MINING SITES

# Opening mining sites geodataframe
mining_gdf = gpd.read_file(mining_path, engine='fiona')

# %% Criando coluna do Código EPSG 

# Pegando zona utm a partir da longitude
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
for epsg in choices.keys():
    
     # Creating sub dataframe and setting respective crs
     choices[epsg] = mining_gdf[mining_gdf['EPSG'] == epsg].to_crs(epsg)
     
     # Creating buffers in km and converting to WGS 84
     choices[epsg]['buffer_2km'] = choices[epsg].buffer(2000).to_crs(4326)
     choices[epsg]['buffer_5km'] = choices[epsg].buffer(5000).to_crs(4326)
     
     # Reprojecting geometry of each sub dataframe to WGS 84
     choices[epsg] = choices[epsg].to_crs(4326)


# Concatenating sub gds back to main gdf
mining_gdf = gpd.GeoDataFrame(pd.concat([choices[df] for df in choices])) 

del epsg, choices


# %% CONCATENATING LANDFILL AND OTHER INDUSTRIAL ACTIVITIES
industrial_gdf = pd.concat([industrial_gdf,landfill_gdf, mining_gdf]).reset_index()

del landfill_gdf, mining_gdf

industrial_gdf.loc[~pd.isna(industrial_gdf['Nome']),
                   'Razão Social'] = industrial_gdf['Nome']
industrial_gdf.loc[~pd.isna(industrial_gdf['NOME']),
                   'Razão Social'] = industrial_gdf['NOME']

industrial_gdf.drop(columns=['Nome', 'NOME'], inplace=True)

# =============================================================================
# fig, ax = plt.subplots(figsize=(10,10))
# #industr/ial_gdf.plot(ax=ax)
# industrial_gdf['buffer_2km'].plot(ax=ax, facecolor='none')
# industrial_gdf['buffer_5km'].plot(ax=ax, facecolor='none')
# =============================================================================

