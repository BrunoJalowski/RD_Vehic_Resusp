#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar 21 11:46:24 2025

@author: brunojalowski
"""
from main import gdf
import emission_factors as ef

#%% PAVED ROADS
pm_list = [2.5, 10, 30]

# Emission factor in g/VKT
for pm in pm_list:
    pm_str = str(pm).replace(".","")
    gdf.loc[gdf['surface'] == 'paved', f'EF{pm_str}'] = (
        ef.ef_paved_roads(pm,
                          gdf.loc[:, 'silt_loading'],
                          gdf.loc[:, 'average_weight']))

#%% UNPAVED INDUSTRIAL
for pm in pm_list:
    pm_str = str(pm).replace(".","")
    
    # Emission factor in lb/VMT

    (
     gdf.loc[(gdf['surface'] == 'unpaved') &
             (gdf['subcategory'] == 'industrial'),
             f'EF{pm_str}']
    ) = ef.ef_unpaved_industrial(pm, 
                                 gdf.loc[:, 'silt_fraction'],
                                 gdf.loc[:, 'average_weight'])
    
    # Conversion from lb/VMT to g/VKT 
    (
     gdf.loc[(gdf['surface'] == 'unpaved') &
            (gdf['subcategory'] == 'industrial'),
            f'EF{pm_str}']
    ) = ef.lbvmt_to_gvkt(gdf.loc[(gdf['surface'] == 'unpaved') &
                                 (gdf['subcategory'] == 'industrial'),
                                 f'EF{pm_str}']
                        )


#%% UNPAVED OPEN ACCESS
"""This section only calculates an intermediate factor used in the emission
factor formula.
    This is done to process all information possible without the temporal
    variability of the soil moisture content."""
    
# Intermediate factor
for pm in pm_list:
    pm_str = str(pm).replace(".","")
    (gdf.loc[(gdf['surface'] == 'unpaved') &
             (gdf['subcategory'] == 'open access'),
             f'EF{pm_str}']
    ) = ef.intermediate_factor_unpaved_public(pm, 
                             gdf.loc[:, 'silt_fraction'],
                             (gdf.loc[:, 'traffic_level'] *
                             0.621371))  # conversao km/h para mph
                             
                             


                                 
#%% UNPAVED OPEN ACCESS EMISSION FACTOR
# =============================================================================
# for pm in pm_list:
#     pm_str = str(pm).replace(".","")
#     (gdf.loc[(gdf['surface'] == 'unpaved') &
#              (gdf['subcategory'] == 'open access'),
#              f'EF{pm_str}']
#     ) = ef.ef_unpaved_public(pm, 
#                              gdf.loc[:, 'silt_fraction'],
#                              (gdf.loc[:, 'traffic_level'] *
#                              0.621371),  # conversao km/h para mph
#                              gdf.loc[:, 'soil_moisture'])
#                              
#     # Conversion from lb/VMT to g/VKT 
#     (
#      gdf.loc[(gdf['surface'] == 'unpaved') &
#             (gdf['subcategory'] == 'open access'),
#             f'EF{pm_str}']
#     ) = ef.lbvmt_to_gvkt(gdf.loc[(gdf['surface'] == 'unpaved') &
#                                  (gdf['subcategory'] == 'open access'),
#                                  f'EF{pm_str}']
#                         )                                 
#                                  
# =============================================================================
#%% RAINFALL CORRECTION   
# =============================================================================
# for pm in pm_list:
#     pm_str = str(pm).replace(".","")
#     
#     # Paved rainfall correction
#     (
#         gdf.loc[gdf['surface'] == 'paved', f'EF{pm_str}_corrected']
#     ) = ef.paved_rainfall_correction(gdf[f'EF{pm_str}'], 0, 365)
#     
#     # Unpaved rainfall correction
#     (
#         gdf.loc[gdf['surface'] == 'unpaved', f'EF{pm_str}_corrected']
#     ) = ef.unpaved_rainfall_correction(gdf[f'EF{pm_str}'], 0, 365)
# =============================================================================
                             

#%% EMISSIONS (g/s)

# =============================================================================
# # Taxa de emissão de Pm2.5 por trecho de via (g/s) ----------------------
# for pm in pm_list:
#     pm_str = str(pm).replace(".","")
#     gdf.loc[:, f'{pm_str}_emission'] = (gdf.loc[:,'vkt'] *
#                                         gdf.loc[:, f'EF{pm_str}_corrected'] / 
#                                         3600)
# =============================================================================

