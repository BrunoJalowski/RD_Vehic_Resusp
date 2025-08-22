#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Aug 11 14:46:07 2025

@author: brunojalowski
"""
import pandas as pd
from Industrial_Sites import buffer_amort, buffer_ind
import geopandas as gpd
from road_preprocess import gdf
from trafficdata.utils.geometries import split_lines_vectorized
from vehicular_weight import vehicular_weight

#%% Paths
fleet_path = ('/home/brunojalowski/Documentos/RD_Vehic_Resusp/dados_entrada/'
              'FrotapormunicipioetipoDezembro2024.xlsx')

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


# %% SEGMENTING ALL ROADS WITH BRAZILIAN MUNICIPALITIES'S BOUNDARIES

# Reading municipality layer 
cities_BR = gpd.read_file("/home/brunojalowski/Documentos/RD_Vehic_Resusp/"
                          "dados_entrada/BR_Municipios_2024.shp")

# Creating layer with boundaries
cities_BR_bound = gpd.GeoDataFrame(data=cities_BR,
                                   geometry=cities_BR.boundary)
# Matching crs with roads_templates
cities_BR_bound.to_crs(4326, inplace=True)
cities_BR.to_crs(4326, inplace=True)

# Splitting roads by municipality
roads_template = split_lines_vectorized(roads_template, cities_BR_bound.explode())


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


























# %% ASSIGNING MUNICIPALITY TO EACH ROAD

# filtering with sjoin for intersection
candidates = gpd.sjoin(cities_BR,
                       roads_template,
                       how='inner',
                       predicate='intersects')

geoms_for_intersect_01 = (cities_BR
                          .loc[candidates.index]
                          .reset_index(drop=False))

geoms_for_intersect_02 = (roads_template
                          .loc[candidates['index_right']]
                          .reset_index(drop=False))
del candidates

# Getting all roads that intersect with buffers 
intersected = geoms_for_intersect_01.intersection(geoms_for_intersect_02)

# Filtering points from result
roads_cities = intersected.loc[intersected
                               .geometry
                               .geom_type == 'LineString']

roads_cities = geoms_for_intersect_02.loc[roads_cities.index]
roads_cities['CD_MUN'] = (geoms_for_intersect_01['CD_MUN']
                          .loc[intersected.index])

roads_cities.geometry = intersected.loc[intersected
                                        .geometry
                                        .geom_type == 'LineString'].geometry

# Assigning city codes 
roads_cities = roads_cities.set_index('index')
roads_template['CD_MUN'] = (
    roads_template.index
    .map(roads_cities['CD_MUN'])
)

del roads_cities, intersected, intersected_roads, geoms_for_intersect_01
del geoms_for_intersect_02, cities_BR_bound

# %% CONVERTING ROAD PROPERTIES PROPORTIONAL TO SEGMENT SIZE
"""This cell aims to convert vkt_per_hour, road_length, vehicle_count and
average_daily_vehicle_count to the respective values for each segment,
following road length proportionality."""



roads_template['road_length']
















# %% LINKING ROADS TO MUNICIPALITIES

"""This file is an intermediary dataframe named frota_categoria_processada, 
after the function adicionando_codigo_ibge_mun_especiais_sem_espaco, from
BRAVES's main code."""

frota_categoria_processada = pd.read_csv('/home/brunojalowski/Documentos/RD_'
                                         'Vehic_Resusp/dados_entrada/frota_'
                                         'categoria_processada.csv')

# Correcting Inconsistencies in city names
corrections = {
    'ARMACAODEBUZIOS': 'ARMACAODOSBUZIOS',
    'BARAODMONTEALTO': 'BARAOD0MONTEALTO',
    'BRASOPOLIS': 'BRAZOPOLIS',
    'EMBU': 'EMBUDASARTES',
    'GOUVEA': 'GOUVEIA',
    'NOVADOMAMORE': 'NOVAMAMORE',
    'POXOREO': 'POXOREU'
    }

frota_categoria_processada['MUNICIPIO'] = (
    frota_categoria_processada['MUNICIPIO']
    .replace(corrections)
    )


# Adding city name to vehicular weight dataframe
mean_vehicular_weight = vehicular_weight(fleet_path)

# Dropping cities without name or code
mean_vehicular_weight = (
    mean_vehicular_weight
    .loc[mean_vehicular_weight['MUNICIPIO'] != 'MUNICIPIONAOINFORMADO']
)

# Merging vehicle weight and city names
mean_vehicular_weight = pd.merge(mean_vehicular_weight,
                                 frota_categoria_processada[['UF',
                                                             'MUNICIPIO',
                                                             'CODIGO IBGE']],
                                 on=['UF','MUNICIPIO'],
                                 how='left')

# Adding IBGE code for "IBITIUVA"
mean_vehicular_weight.loc[mean_vehicular_weight['MUNICIPIO'] == 'IBITIUVA',
                          'CODIGO IBGE'] = 3521508

mean_vehicular_weight['CODIGO IBGE'] = (
    mean_vehicular_weight['CODIGO IBGE']
    .astype(int)
    .astype(str)
    )

# Renaming CODIGO IBGE to CD_MUN
mean_vehicular_weight.rename(columns={"CODIGO IBGE":"CD_MUN"}, inplace=True)

# Adding city name to road segments
roads_template = pd.merge(roads_template,
                          mean_vehicular_weight[['average_weight', 'CD_MUN']],
                          on=['CD_MUN'],
                          how='left')