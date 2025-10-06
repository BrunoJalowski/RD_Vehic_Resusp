#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar 21 11:46:24 2025

@author: brunojalowski
"""
from main import gdf
import emission_factors as ef

   
#%% PM2.5
# Unpaved Industrial ------------------------
# Emission factor in lb/VMT
(
 gdf.loc[(gdf['surface'] == 'unpaved') &
        (gdf['subcategory'] == 'industrial'),'EF25']
) = ef.emission_unpaved_industrial(2.5, 
                                   gdf.loc[:, 'silt_fraction'],
                                   gdf.loc[:, 'average_weight'])

# Conversion from lb/VMT to g/VKT
(
 gdf.loc[(gdf['surface'] == 'unpaved') &
        (gdf['subcategory'] == 'industrial'),'EF25']
) = ef.lbvmt_to_gvkt(gdf.loc[(gdf['surface'] == 'unpaved') &
                             (gdf['subcategory'] == 'industrial'),
                             'EF25']
                    )
                        
## Unpaved Open Access ----------------------
# Emission factor in lb/VMT
(
    gdf.loc[(gdf['surface'] == 'unpaved') &
            (gdf['subcategory'] == 'open access'), 'EF25']
) = ef.emission_unpaved_public(2.5, gdf.loc[:, 'silt_fraction'],
                               (gdf.loc[:, 'avg_traffic_level'] *
                                0.621371),  # conversao km/h para mph
                               gdf.loc[:, 'soil_moisture'])

# Conversion from lb/VMT to g/VKT
(
    gdf.loc[(gdf['surface'] == 'unpaved') &
            (gdf['subcategory'] == 'open access'), 'EF25']
) = ef.lbvmt_to_gvkt(gdf.loc[(gdf['surface'] == 'unpaved') &
                             (gdf['subcategory'] == 'open access'),
                             'EF25']
                    )

## Paved -----------------------------------
# Emission factor in g/VKT
(
    gdf.loc[gdf['surface'] == 'paved', 'EF25']
) = ef.emission_paved_roads(2.5,
                            gdf.loc[:, 'silt_loading'],
                            gdf.loc[:, 'average_weight'])
                            
## Correção da emissão pela pluviosidade --------------------------
# Unpaved
(
    gdf.loc[gdf['surface'] == 'unpaved', 'EF25_corrected']
) = ef.unpaved_rainfall_correction(gdf['EF25'], 0, 365)

# Paved
(
    gdf.loc[gdf['surface'] == 'paved', 'EF25_corrected']
) = ef.paved_rainfall_correction(gdf['EF25'], 0, 365)

# Taxa de emissão de Pm2.5 por trecho de via (g/s) ----------------------
gdf.loc[:, '25_emission'] = (gdf.loc[:,'vkt_per_hour'] *
                             gdf.loc[:, 'EF25_corrected'] / 3600)


# %% PM10
# Unpaved Industrial ------------------------
# Emission factor in lb/VMT
(
 gdf.loc[(gdf['surface'] == 'unpaved') &
        (gdf['subcategory'] == 'industrial'),'EF10']
) = ef.emission_unpaved_industrial(10, 
                                   gdf.loc[:, 'silt_fraction'],
                                   gdf.loc[:, 'average_weight'])

# Conversion from lb/VMT to g/VKT
(
 gdf.loc[(gdf['surface'] == 'unpaved') &
        (gdf['subcategory'] == 'industrial'),'EF10']
) = ef.lbvmt_to_gvkt(gdf.loc[(gdf['surface'] == 'unpaved') &
                             (gdf['subcategory'] == 'industrial'),
                             'EF10']
                    )
                        
## Unpaved Open Access ----------------------
# Emission factor in lb/VMT
(
    gdf.loc[(gdf['surface'] == 'unpaved') &
            (gdf['subcategory'] == 'open access'), 'EF10']
) = ef.emission_unpaved_public(10, gdf.loc[:, 'silt_fraction'],
                               (gdf.loc[:, 'avg_traffic_level'] *
                                0.621371),  # conversao km/h para mph
                               gdf.loc[:, 'soil_moisture'])

# Conversion from lb/VMT to g/VKT
(
    gdf.loc[(gdf['surface'] == 'unpaved') &
            (gdf['subcategory'] == 'open access'), 'EF10']
) = ef.lbvmt_to_gvkt(gdf.loc[(gdf['surface'] == 'unpaved') &
                             (gdf['subcategory'] == 'open access'),
                             'EF10']
                    )

## Paved -----------------------------------
# Emission factor in g/VKT
(
    gdf.loc[gdf['surface'] == 'paved', 'EF10']
) = ef.emission_paved_roads(10,
                            gdf.loc[:, 'silt_loading'],
                            gdf.loc[:, 'average_weight'])
                     
                            
# Correção da emissão pela pluviosidade --------------------------
# Unpaved
(
    gdf.loc[gdf['surface'] == 'unpaved', 'EF10_corrected']
) = ef.unpaved_rainfall_correction(gdf['EF10'], 0, 365)

# Paved
(
    gdf.loc[gdf['surface'] == 'paved', 'EF10_corrected']
) = ef.paved_rainfall_correction(gdf['EF10'], 0, 365)


# Taxa de emissão de Pm10 por trecho de via (g/s) ----------------------
gdf.loc[:, '10_emission'] = (gdf.loc[:,'vkt_per_hour'] *
                             gdf.loc[:, 'EF10_corrected'] / 3600)

# %% PM30
# Unpaved Industrial ------------------------
# Emission factor in lb/VMT
(
 gdf.loc[(gdf['surface'] == 'unpaved') &
        (gdf['subcategory'] == 'industrial'),'EF30']
) = ef.emission_unpaved_industrial(30, 
                                   gdf.loc[:, 'silt_fraction'],
                                   gdf.loc[:, 'average_weight'])

# Conversion from lb/VMT to g/VKT
(
 gdf.loc[(gdf['surface'] == 'unpaved') &
        (gdf['subcategory'] == 'industrial'),'EF30']
) = ef.lbvmt_to_gvkt(gdf.loc[(gdf['surface'] == 'unpaved') &
                             (gdf['subcategory'] == 'industrial'),
                             'EF30']
                    )
                        
## Unpaved Open Access ----------------------
# Emission factor in lb/VMT
(
    gdf.loc[(gdf['surface'] == 'unpaved') &
            (gdf['subcategory'] == 'open access'), 'EF30']
) = ef.emission_unpaved_public(30,
                               gdf.loc[:, 'silt_fraction'],
                               (gdf.loc[:, 'avg_traffic_level'] *
                                0.621371),  # conversao km/h para mph
                               gdf.loc[:, 'soil_moisture'])

# Conversion from lb/VMT to g/VKT
(
    gdf.loc[(gdf['surface'] == 'unpaved') &
            (gdf['subcategory'] == 'open access'), 'EF30']
) = ef.lbvmt_to_gvkt(gdf.loc[(gdf['surface'] == 'unpaved') &
                             (gdf['subcategory'] == 'open access'),
                             'EF30']
                    )

## Paved -----------------------------------
# Emission factor in g/VKT
(
    gdf.loc[gdf['surface'] == 'paved', 'EF30']
) = ef.emission_paved_roads(30,
                            gdf.loc[:, 'silt_loading'],
                            gdf.loc[:, 'average_weight'])
                            
# Correção da emissão pela pluviosidade --------------------------
# Unpaved
(
    gdf.loc[gdf['surface'] == 'unpaved', 'EF30_corrected']
) = ef.unpaved_rainfall_correction(gdf['EF30'], 0, 365)

# Paved
(
    gdf.loc[gdf['surface'] == 'paved', 'EF30_corrected']
) = ef.paved_rainfall_correction(gdf['EF30'], 0, 365)



# Taxa de emissão Pm30 por trecho de via (g/s) ----------------------
gdf.loc[:, '30_emission'] = (gdf.loc[:,'vkt_per_hour'] *
                             gdf.loc[:, 'EF30_corrected'] / 3600)

