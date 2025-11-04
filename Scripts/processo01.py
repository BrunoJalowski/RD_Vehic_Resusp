#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Aug 11 14:46:07 2025

@author: brunojalowski
"""
import pandas as pd
import geopandas as gpd
from trafficdata.utils.geometries import split_lines_vectorized
from pathlib import Path
from utils_processo01 import intersect_by_sjoin
from multiprocessing import Pool
import numpy as np
from get_geodesic_line_length import get_geodesic_line_length
from functools import partial
from pyproj import Geod


#%% Paths
inputs_path = Path('./inputs').resolve()

outputs_path = Path('./outputs')

N_JOBS = 6

buffer_ind_path = inputs_path / 'buffer_ind.gpkg'

buffer_amort_path = inputs_path / 'buffer_amort.gpkg'

# roads_path = inputs_path / "processed_roads_dissolved.parquet"
roads_path = inputs_path / "2025-05-13_all_geofabrik_roads.parquet"

cities_BR_path = inputs_path / "BR_Municipios_2024.shp"

mcip_grid_path = inputs_path / 'old_mesh_20km.gpkg'

#%%
# Reading
roads = gpd.read_parquet(path=roads_path)

buffer_ind = gpd.read_file(buffer_ind_path)
buffer_amort = gpd.read_file(buffer_amort_path)

mcip_grid = gpd.read_file(mcip_grid_path)
mcip_grid['cell_id'] = mcip_grid.index.astype(str)

# Reading municipality layer 
cities_BR = gpd.read_file(cities_BR_path)

# Matching crs with roads_templates
cities_BR.to_crs(4326, inplace=True)
cities_BR = cities_BR[['CD_MUN','geometry']].set_index('CD_MUN')
cities_BR.index.name = None

# Selecting columns
roads = roads.reset_index(drop=False)
roads = roads.loc[:, ['osm_id','lanes','surface', 'geometry']]


def run_slicing(roads_gdf):

    # SEGMENTING ALL ROADS WITH INDUSTRIAL BUFFERS ===========================

    buffer_ind_bound = gpd.GeoDataFrame(data=buffer_ind['silt_loading'],
                                        geometry=buffer_ind.boundary)
    buffer_amort_bound = gpd.GeoDataFrame(data=buffer_amort['silt_loading'],
                                        geometry=buffer_amort.boundary)


    # Splitting roads by wider buffers
    roads_template = split_lines_vectorized(roads_gdf,
                                            buffer_amort_bound.explode())
    del roads_gdf
    # Splitting roads by more restrict buffers
    roads_template = split_lines_vectorized(roads_template,
                                            buffer_ind_bound.explode())

    """The roads_template variable will be used as the default layer for roads
    from this point on. All new road information will be assigned to this
    GeoDataFrame via osm_id"""


    # Splitting roads by MCIP grid
    roads_template = intersect_by_sjoin(roads_template, mcip_grid)

    # Splitting roads by municipality
    roads_template = intersect_by_sjoin(roads_template, cities_BR)


    # Creating unique id for every road segment
    roads_template['segment_id'] = roads_template.index.astype(str)

    # INTERSECTING INTERNAL BUFFERS =========================================

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

    roads_ind.geometry = intersected_ind.loc[
        intersected_ind
        .geometry
        .geom_type == 'LineString'].geometry

    del intersected_ind, geoms_for_intersect_01, geoms_for_intersect_02


    # INTERSECTING EXTERNAL BUFFERS =========================================

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


    # Concatenating intersected gdfs for final silt loading values 
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

    return roads_template


chunks = np.array_split(roads, N_JOBS)

# Executa em paralelo
with Pool(processes=N_JOBS) as p:
    results = p.map(
        run_slicing, chunks)

# Combina resultados
result = gpd.GeoDataFrame(
    pd.concat(results, ignore_index=True),
    geometry='geometry',
    crs=roads.crs
)


#%% CALCULATING ROAD SEGMENT LENGTH ==========================================

# Removing GeometryCollection geometries 
result = result[
    result.geometry.type.isin(['LineString', 'MultiLineString'])
]

# Setting source datum from WGS84 and SIRGAS2000
GEOD = Geod(ellps="GRS80")

# Setting up partial function
length_funct = partial(get_geodesic_line_length, geod=GEOD)

# Creating cell_road_length column
result['segment_length'] = result.geometry \
    .apply(length_funct)

# Saving to parquet
result.to_parquet(inputs_path / 'roads_template_old_grid.parquet')
