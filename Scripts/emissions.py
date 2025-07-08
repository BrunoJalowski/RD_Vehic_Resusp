#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar 21 11:46:24 2025

@author: brunojalowski
"""
from main import gdf, vehicular_weight
import emission_factors as ef

# %% EMISSÕES VIAS NÃO PAVIMENTADAS ACESSO PÚBLICO

# Dados iniciais via não pavimentada

# ## PM2.5
# Fator de emissão PM2.5 em lb/VMT
(
    gdf.loc[gdf['surface'] == 'unpaved', 'EF25']
) = ef.emission_unpaved_public(2.5, gdf.loc[:, 'silt_fraction'],
                               (gdf.loc[:, 'avg_traffic_level'] *
                                0.621371),  # conversao km/h para mph
                               gdf.loc[:, 'soil_moisture'])

# Conversão de lb/VMT para g/VKT
(
    gdf.loc[gdf['surface'] == 'unpaved', 'EF25']
) = gdf.loc[:, 'EF25'].apply(ef.lbvmt_to_gvkt)

# Correção da emissão pela pluviosidade
(
    gdf.loc[gdf['surface'] == 'unpaved', 'EF25_corrected']
) = ef.unpaved_rainfall_correction(gdf['EF25'], 0, 365)

# Taxa de emissão de Pm2.5 por trecho de via (g/s)
(
    gdf.loc[gdf['surface'] == 'unpaved', '25_emission']
) = (gdf.loc[gdf['surface'] == 'unpaved', 'vkt_per_hour'] *
     gdf.loc[gdf['surface'] == 'unpaved', 'EF25_corrected'] /
     3600)


# ## PM10
# Fator de emissão PM10 em lb/VMT
(
    gdf.loc[gdf['surface'] == 'unpaved', 'EF10']
) = ef.emission_unpaved_public(10,
                               gdf.loc[:, 'silt_fraction'],
                               (gdf.loc[:, 'avg_traffic_level'] *
                                0.621371),  # conversao km/h para mph
                               gdf.loc[:, 'soil_moisture'])

# Conversão de lb/VMT para g/VKT
(
    gdf.loc[gdf['surface'] == 'unpaved', 'EF10']
) = gdf.loc[:, 'EF10'].apply(ef.lbvmt_to_gvkt)

# Correção da emissão pela pluviosidade
(
    gdf.loc[gdf['surface'] == 'unpaved', 'EF10_corrected']
) = ef.unpaved_rainfall_correction(gdf['EF10'], 0, 365)

# Taxa de emissão de Pm10 por trecho de via (g/s)
(
    gdf.loc[gdf['surface'] == 'unpaved', '10_emission']
) = (gdf.loc[gdf['surface'] == 'unpaved', 'vkt_per_hour'] *
     gdf.loc[gdf['surface'] == 'unpaved', 'EF10_corrected'] /
     3600)


# ## PM30
# Fator de emissão PM30 em lb/VMT
(
    gdf.loc[gdf['surface'] == 'unpaved', 'EF30']
) = ef.emission_unpaved_public(30,
                               gdf.loc[:, 'silt_fraction'],
                               (gdf.loc[:, 'avg_traffic_level'] *
                                0.621371),  # conversao km/h para mph
                               gdf.loc[:, 'soil_moisture'])

# Conversão de lb/VMT para g/VKT
(
    gdf.loc[gdf['surface'] == 'unpaved', 'EF30']
) = gdf.loc[:, 'EF30'].apply(ef.lbvmt_to_gvkt)


# Correção da emissão pela pluviosidade
(
    gdf.loc[gdf['surface'] == 'unpaved', 'EF30_corrected']
) = ef.unpaved_rainfall_correction(gdf['EF30'], 0, 365)

# Taxa de Emissão de Pm30 por trecho de via (g/s)
(
    gdf.loc[gdf['surface'] == 'unpaved', '30_emission']
) = (gdf.loc[gdf['surface'] == 'unpaved', 'vkt_per_hour'] *
     gdf.loc[gdf['surface'] == 'unpaved', 'EF30_corrected'] /
     3600)

# %% EMISSÕES VIAS PAVIMENTADAS

# Dados iniciais
weight = (
    vehicular_weight
    .loc[vehicular_weight['MUNICIPIO'] == 'FLORIANOPOLIS', "average_weight"]
    .values[0]
)

# ## PM2.5
# Fator de emissão PM2.5 em g/VKT
(
    gdf.loc[gdf['surface'] == 'paved', 'EF25']
) = ef.emission_paved_roads(2.5,
                            gdf.loc[:, 'silt_loading'],
                            weight)

# Correção da emissão pela pluviosidade
(
    gdf.loc[gdf['surface'] == 'paved', 'EF25_corrected']
) = ef.paved_rainfall_correction(gdf['EF25'],
                                 0,
                                 365)

# Taxa de emissão de Pm2.5 por trecho de via (g/hora)
(
    gdf.loc[gdf['surface'] == 'paved', '25_emission']
) = (gdf.loc[gdf['surface'] == 'paved', 'vkt_per_hour'] *
     gdf.loc[gdf['surface'] == 'paved', 'EF25_corrected'])


# ## PM10
# Fator de emissão PM10 em g/VKT
(
    gdf.loc[gdf['surface'] == 'paved', 'EF10']
) = ef.emission_paved_roads(10,
                            gdf.loc[:, 'silt_loading'],
                            weight)

# Correção da emissão pela pluviosidade
(
    gdf.loc[gdf['surface'] == 'paved', 'EF10_corrected']
) = ef.paved_rainfall_correction(gdf['EF10'],
                                 0,
                                 365)

# Taxa de emissão de Pm10 por trecho de via (g/hora)
(
    gdf.loc[gdf['surface'] == 'paved', '10_emission']
) = (gdf.loc[gdf['surface'] == 'paved', 'vkt_per_hour'] *
     gdf.loc[gdf['surface'] == 'paved', 'EF10_corrected'])


# ## PM30
# Fator de emissão PM30 em g/VKT
(
    gdf.loc[gdf['surface'] == 'paved', 'EF30']
) = ef.emission_paved_roads(30,
                            gdf.loc[:, 'silt_loading'],
                            weight)

# Correção da emissão pela pluviosidade
(
    gdf.loc[gdf['surface'] == 'paved', 'EF30_corrected']
) = ef.paved_rainfall_correction(gdf['EF30'],
                                 0,
                                 365)

# Taxa de Emissão de Pm30 por trecho de via (g/hora)
(
    gdf.loc[gdf['surface'] == 'paved', '30_emission']
) = (gdf.loc[gdf['surface'] == 'paved', 'vkt_per_hour'] *
     gdf.loc[gdf['surface'] == 'paved', 'EF30_corrected'])
