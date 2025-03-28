# -*- coding: utf-8 -*-
"""
Created on Fri Dec 20 10:22:09 2024

@author: bruno
"""

#%%Importando pacotes
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
#%%Definindo caminhos das pastas de trabalho

# Pasta de dados de entrada
inputsPath = 'C:\\Users\\bruno\\Desktop\\LCQAr\\RD_Vehic_Resusp\\BRAVES\\ReferenceCities_Popul&Dens\\Inputs'

# Pasta de outputs
outputsPath = 'C:\\Users\\bruno\\Desktop\\LCQAr\\RD_Vehic_Resusp\\BRAVES\\ReferenceCities_Popul&Dens\\Outputs'

# Pasta de trabalho

scriptsPath = 'C:\\Users\\bruno\\Desktop\\LCQAr\\RD_Vehic_Resusp\\BRAVES\\ReferenceCities_Popul&Dens\\Scripts'


#%%Lendo malha municipal com desidade populacional do Censo IBGE 2022

citiesBR = gpd.read_file(inputsPath + '\\' + 'sidra_4714_DensDemog_HabKm2_munic_22_polPolygon.shp')
citiesBR = citiesBR.to_crs(4326)


#%%Criando layer de pontos das estações de referencia

# Lê o arquivo csv e cria um DataFrame
stationsBR = pd.read_csv(inputsPath + '\\' + "Monitoramento_QAr_BR_latlon.csv", encoding='Latin-1')

# Transforma o DataFrame em um GeoDataFrame a partir das colunas longitude e latitude
stationsBR = gpd.GeoDataFrame(stationsBR,
                              geometry= gpd.points_from_xy(stationsBR.LONGITUDE, stationsBR.LATITUDE),
                              crs="EPSG:4326")

# Filtra apenas as estações de referência
stationsBR = stationsBR.loc[(stationsBR['MÉTODO'] == 'Referência')]

stationsBR.head()


#%%Removendo linhas duplicadas, mantendo as informações da primeira apenas

stationsBR = stationsBR.dissolve(by='ESTAÇÃO')
stationsBR.head()


#%%Plotando pontos e cidades do Brasil

fig, ax = plt.subplots()
citiesBR.plot(ax=ax)
stationsBR.plot(color='r',ax=ax, markersize=3)


#%%Cria GeoDataFrame apenas com as cidades que têm estações de referência

# Realiza o spatial join entre as estações e as cidades
joined = gpd.sjoin(stationsBR,
                   citiesBR,
                   how="inner",  # retorna só as linhas de citiesBR que tem estações de stationsBR dentro delas
                   predicate="within"   #https://shapely.readthedocs.io/en/stable/reference/shapely.within.html#shapely.within
                   )

# Pega as cidades que têm no mínimo uma estação
referenceCities = citiesBR[citiesBR.index.isin(joined['index_right'].unique())]

# Conta o numero de estações de cada cidade
station_count_by_city = joined.groupby('index_right').size()

# Cria uma coluna com o número de estações de cada cidade
referenceCities.loc[:, 'st_count'] = referenceCities.index.map(station_count_by_city).fillna(0)

# Colocando o nome das cidades como indice
referenceCities = referenceCities.set_index('Nome')

# Salvando camada de Cidades com estações em arquivo shp
referenceCities.to_file(outputsPath + '\\' +'referenceCities.shp')



#%%Plotando as estações da cidade com mais estações para confirmar que a contagem ta certa
# pois o número máximo de estações em uma mesma cidade foi de 92 estações no RJ e não pensei que fosse verdade

# Cidade com o número máximo de estações
max_station_city = referenceCities.loc[referenceCities['st_count'] == referenceCities['st_count'].max()]

# Estações dentro da cidade
stations_in_max_city = joined[joined['index_right'] == max_station_city.index[0]]

# Plotando
fig, ax = plt.subplots()
max_station_city.plot(ax=ax, color='grey')
stations_in_max_city.plot(ax=ax, color='blue', markersize=5, label="Estações")

plt.legend()

#%%Plotando apenas as cidades com estações e as estações

fig, ax = plt.subplots()
referenceCities.plot(ax=ax)
stationsBR.plot(color='r',ax=ax, markersize=3)


#%%Criando camadas de areas urbanas

# Lê camada com todas as áreas urbanas do BR
urbanAreas = gpd.read_file(inputsPath + '\\' + 'areas_urbanas.gpkg')

# Cria camada as áreas urbanas que intersectam as cidades com estações de referência a partir da máscara
priorityAreas = gpd.read_file(inputsPath + '\\' + 'areas_urbanas.gpkg', mask= referenceCities)

# Salvando área urbana prioritária em arquivo shp
priorityAreas.to_file(outputsPath + '\\' + 'priorityAreas.shp')


#%%Plotando as áreas urbanas e prioritárias

fig, ax = plt.subplots()
referenceCities.plot(ax=ax)
urbanAreas.plot(ax=ax, color='g')
priorityAreas.plot(ax=ax,color='r')







