#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb 11 11:42:04 2025

@author: brunojalowski
"""
# %% IMPORTING MODULES ========================================================
import geopandas as gpd
from pathlib import Path
import glob
import pandas as pd

from reclassify_surface import reclassify_surface
from silt_loading_by_adt import silt_loading_by_adt
import ef_functions as ef
from is_leap_year import is_leap_year


# %% PATHS ===================================================================
inputs_path = Path('../inputs').resolve()

outputs_path = Path('../outputs').resolve()

process04_outputs_path = outputs_path / 'process04'

flow_path = inputs_path / 'traffic_data'

roads_template_path = inputs_path / 'roads_template_old_grid_with_sF.parquet'

weight_path = outputs_path / 'vehicular_weight'


#%%
# Listing years
years = [int(str(path).split('/')[-1]) 
         for path 
         in list(Path(flow_path).glob('*/'))]

# Sorting years in chronologicl order
years = sorted(years, reverse=True) #FIXME RETIRAR O REVERSE

# Iterating over all years available in chronological order
for year in years:
    year_input_folder = Path(flow_path / f'{year}')
    year_output_folder = process04_outputs_path / f'{year}'
    
    # Creating folder for the year if non existant
    if not year_output_folder.exists():
        year_output_folder.mkdir(parents=True, exist_ok=True)
        
    # Listing all months available
    months = [int(str(path).split('/')[-1]) 
              for path 
              in list(Path(year_input_folder).glob('*/'))
              ]
    
    # Sorting them in cronological order
    months = sorted(months)
    
    # Dict with number of days by month
    days_by_month = {
        1: 31, 2: 28, 3: 31, 4: 30,
        5: 31, 6: 30, 7: 31, 8: 31, 
        9: 30, 10: 31, 11: 30, 12: 31
        }
    
    # Changes number of days for february if year is a leap year
    if is_leap_year(year):
        days_by_month[2] = 29
    

    # Iterating over month folders
    for month in months:
        month_input_folder = year_input_folder / f'{month}'
        month_output_folder = year_output_folder / f'{month}'

        # Creating folder for the year if non existant
        if not month_output_folder.exists():
            month_output_folder.mkdir(parents=True, exist_ok=True)
        
    
        # SETTING UP AVERAGE WEIGHT VALUES LIST =============================
        
        # Reading average weight df
        weight_df = pd.read_parquet(weight_path /
                                    f'peso_medio_{year}.parquet')
        
        # Selecting city weight column for the year
        col = 'average_weight_'
        city_weight = weight_df.loc[:, [col + str(month),'CODIGO IBGE']]
        
        del weight_df

        
        # Listing all cities paths for this timestep
        cities_paths = glob.glob(str(month_input_folder / '*.parquet'))

        
        # Iterating over all cities on this year and this month
        for city_path in cities_paths:
            
            # Establishing city id
            city_id = int(str(city_path).split('/')[-1].split('.')[0])
            

            # Iterates over all days available for that month is order
            for day in range(1, days_by_month[month] + 1):
                # FLOW DATA ====================================================
                
                # Reading geodataframe
                gdf = (pd
                       .read_parquet(city_path)
                       .astype({'osm_id': int,
                                'vehicle_count': float,
                                'adt': float,
                                'traffic_level': float,
                                'city_id': int,
                                'cell_id': int}
                               )
                       )
 

                # Selecting only timesteps for the day
                gdf = gdf.loc[gdf.index.day == day, :]
                
                # Transforming datetime index in column
                gdf.reset_index(inplace=True, drop=False)

                # Creating average weight column
                gdf['avg_weight'] = city_weight.loc[
                    city_weight['CODIGO IBGE'] == city_id,
                    f'average_weight_{month}'
                    ].values[0]

                
                # Reading file with all road segments with static information
                roads_template = (gpd
                                  .read_parquet(roads_template_path)
                                  .astype({'osm_id': int,
                                           'segment_id': str,
                                           'silt_loading': float,
                                           'segment_length': float,
                                           'CD_MUN': int,
                                           'cell_id': int,
                                           'silt_fraction': float,
                                           'surface': str,
                                           'lanes': int}
                                          ))

                # Removing GeometryCollection geometries 
                roads_template = roads_template[
                    roads_template.geometry.type.isin(['LineString', 
                                                       'MultiLineString'])
                    ]
                
                roads_template.rename(columns={'CD_MUN':'city_id'},
                                      inplace=True)
                
                               
                # Applying segmentation to every timestep
                gdf = gdf.merge(roads_template,
                                how='left',
                                on=['osm_id','city_id','cell_id'])
                
                del roads_template
            
                # Reclassifying surface in paved/unpaved
                gdf = reclassify_surface(gdf)

                # Setting geometry column as geometry
                gdf.set_geometry(col='geometry', crs=4326)
                
                # Calculating silt loading for road segments outside buffers
                gdf = silt_loading_by_adt(gdf)
                
                # Subclassifying unpaved roads in industrial or open access
                gdf.loc[(gdf['silt_loading'].notna()) &
                        (gdf['surface'] == 'unpaved'),
                        'subcategory'] = 'industrial'
                
                gdf.loc[(gdf['silt_loading'].isna()) &
                        (gdf['surface'] == 'unpaved'),
                        'subcategory'] = 'open access'
                
                gdf.loc[gdf['surface'] == 'paved',
                        'subcategory'] = 'paved'
                
                
                # Removing silt loading values from unpaved segments inside 
                # industrial zones since it's not used
                gdf.loc[(gdf['silt_loading'].notna()) &
                        (gdf['surface'] == 'unpaved'), 'silt_loading'] = None
    
    
                # CALCULATING VKT ===========================================
                gdf.loc[:,'vkt'] = (
                    gdf['vehicle_count'] *
                    gdf['segment_length'] /
                    1000
                )
                
                # SEPARATING INTO 2 GDFs ====================================
                '''
                ind_n_paved --> industrial unpaved and paved roads
                open_access --> open access unpaved roads   
                '''
                
                # Unpaved industrial roads and paved roads
                ind_n_paved = gdf.loc[(gdf['subcategory'] == 'industrial') |
                                      (gdf['subcategory'] == 'paved'),
                                      :]
                
                # Unpaved open access roads
                open_access = gdf.loc[gdf['subcategory'] == 'open access']
                
                del gdf
                
                
                # EMISSION FACTOR FOR PAVED ROADS ===========================
                pm_list = [2.5, 10, 30]
                
                # Emission factor in g/VKT
                for pm in pm_list:
                    pm_str = str(pm).replace(".","")
                    condition = ind_n_paved['surface'] == 'paved'
                    
                    ind_n_paved.loc[condition, f'EF{pm_str}'] = (
                        ef.ef_paved_roads(pm,
                                          ind_n_paved.loc[:, 'silt_loading'],
                                          ind_n_paved.loc[:, 'avg_weight']
                                          )
                        )
                
                
                # EMISSION FACTOR FOR UNPAVED INDUSTRIAL ====================
                for pm in pm_list:
                    pm_str = str(pm).replace(".","")
                    
                    # Conditions for selecting unpaved and industrial 
                    conditions = (
                        (ind_n_paved['surface'] == 'unpaved') & 
                        (ind_n_paved['subcategory'] == 'industrial')
                        )
                    
                    # Calculating emission factors in lb/VMT
                    ind_n_paved.loc[conditions, f'EF{pm_str}'] = (
                        ef.ef_unpaved_industrial(
                            pm, 
                            ind_n_paved.loc[:, 'silt_fraction'],
                            ind_n_paved.loc[:, 'avg_weight']
                            )
                        )
                    
                    # Converting from lb/VMT to g/VKT 
                    ind_n_paved.loc[conditions, f'EF{pm_str}'] = (
                        ef.lbvmt_to_gvkt(ind_n_paved
                                         .loc[conditions,f'EF{pm_str}']
                                         )
                        )
                
                
                # CALCULATING EMISSIONS FOR PAVED AND INDUSTRIAL ROADS ======
                for pm in pm_list:
                    pm_str = str(pm).replace(".","")
                    ind_n_paved[f'emission_{pm_str}'] = (
                        ind_n_paved[f'EF{pm_str}'] * ind_n_paved['vkt']
                        )

                
                # AGGREGATING EMISSION BY WEEKDAY, HOUR AND CELL_ID ==========
                ind_n_paved_emissions = (
                    ind_n_paved
                    .groupby([ind_n_paved.date_range,'cell_id'])[
                        ['emission_25',
                         'emission_10',
                         'emission_30']]
                    .aggregate('sum')
                    )
                
                del ind_n_paved
                
                # Setting unit as attribute
                for col in ['emission_25', 'emission_10', 'emission_30']:
                    ind_n_paved_emissions[col].attrs['unit'] = 'g/hour'
                
            
                # Saving to file
                ind_n_paved_emissions.to_parquet(
                    month_output_folder /
                    f'industrialAndPavedEmission_{year}-{month}-{day}_'
                    f'{city_id}.parquet'
                )
                
                
                # INTERMEDIATE FACTOR FOR UNPAVED OPEN ACCESS ===============
                """This section only calculates an intermediate factor used in 
                the emission factor formula.
                   This is done to process all information possible without 
                the temporal variability of the soil moisture content.
                
                """
                
                conv_factor = 0.621371 # conversion km/h -> mph
                
                # Intermediate factor
                for pm in pm_list:
                    pm_str = str(pm).replace(".","")
                    
                    open_access.loc[:, f'EF{pm_str}_partial'] = (
                        ef.intermediate_factor_unpaved_public(
                            pm, 
                            open_access.loc[:, 'silt_fraction'],
                            open_access.loc[:, 'traffic_level'] * conv_factor
                            )  
                        ) 
                    
                    
                    
                # WEIGHTED AVERAGE FOR INTERMEDIATE FACTOR PER CELL =========
                
                # Getting segments without temporal variation
                length_per_cell = (
                    open_access
                    .drop_duplicates(subset=['segment_id'])
                    )
                    
                # Calculating total road length per osm_id
                length_per_cell = (
                    length_per_cell
                    .groupby('cell_id')['segment_length']
                    .sum()
                    )
                
                # Calculating weight factor by segment length
                open_access['weight_factor'] = (
                    open_access['segment_length'] / 
                    open_access['cell_id'].map(length_per_cell)
                    )
                
                # Calculating partial EF for each segment
                for pm in pm_list:
                    pm_str = str(pm).replace(".","")
                    open_access[f'EF{pm_str}_partial_factor'] = (
                        open_access['weight_factor'] *
                        open_access[f'EF{pm_str}_partial'] 
                        )
                
                # Calculating weighted average for vhc/hour/lane/cell
                open_access['avg_flow'] = (
                    open_access['vehicle_count'] / 
                    open_access['lanes'] *
                    open_access['weight_factor']
                    )                

                    
                # Calculating weighted average disaggregated in time
                open_access = (
                    open_access
                    .groupby([open_access.date_range,'cell_id'])
                    [['EF25_partial_factor',
                      'EF10_partial_factor',
                      'EF30_partial_factor',
                      'avg_flow']]
                    .sum()
                    )

                
                # Saving to file
                open_access.to_parquet(
                    month_output_folder / 
                    f'publicPartial_{year}-{month}-{day}_{city_id}.parquet'
                )
                break # Itera em todos os dias
            #break # itera em todas as cidades
        break # itera em todos os meses
    break # itera em todos os anos



