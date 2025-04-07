#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar 21 11:46:24 2025

@author: brunojalowski
"""
from main import gdf_filtered
import emission_factors as ef

#%% EMISSÕES VIAS NÃO PAVIMENTADAS ACESSO PÚBLICO

#Dados iniciais via não pavimentada

### PM2.5
#Fator de emissão PM2.5 em lb/VMT
gdf_filtered.loc[gdf_filtered['surface']=='unpaved','EF25'] = ef.emission_unpaved_public(2.5, gdf_filtered.loc[:,'silt_fraction'], (gdf_filtered.loc[:,'traffic_level'] * 0.621371), gdf_filtered.loc[:,'soil_moisture'])

    #0.621371 é o fator de conversão de km/h para mph

#Conversão de lb/VMT para g/VKT
gdf_filtered.loc[gdf_filtered['surface']=='unpaved','EF25'] = gdf_filtered.loc[:,'EF25'].apply(ef.lbvmt_to_gvkt)

#Correção da emissão pela pluviosidade
gdf_filtered.loc[gdf_filtered['surface']=='unpaved','EF25_corrected'] = ef.unpaved_rainfall_correction(gdf_filtered['EF25'], 100, 365)

#Taxa de emissão de Pm2.5 por trecho de via (g/s)
gdf_filtered.loc[gdf_filtered['surface']=='unpaved','25_emission'] = gdf_filtered.loc[gdf_filtered['surface']=='unpaved','flow'] * gdf_filtered.loc[gdf_filtered['surface']=='unpaved','length']/1000 * gdf_filtered.loc[gdf_filtered['surface']=='unpaved','EF25_corrected'] / 3600


### PM10
#Fator de emissão PM10 em lb/VMT
gdf_filtered.loc[gdf_filtered['surface']=='unpaved','EF10'] = ef.emission_unpaved_public(10, gdf_filtered.loc[:,'silt_fraction'], (gdf_filtered.loc[:,'traffic_level'] * 0.621371), gdf_filtered.loc[:,'soil_moisture'])

    #0.621371 é o fator de conversão de km/h para mph

#Conversão de lb/VMT para g/VKT
gdf_filtered.loc[gdf_filtered['surface']=='unpaved','EF10'] = gdf_filtered.loc[:,'EF10'].apply(ef.lbvmt_to_gvkt)

#Correção da emissão pela pluviosidade
gdf_filtered.loc[gdf_filtered['surface']=='unpaved','EF10_corrected'] = ef.unpaved_rainfall_correction(gdf_filtered['EF10'], 100, 365)

#Taxa de emissão de Pm10 por trecho de via (g/s)
gdf_filtered.loc[gdf_filtered['surface']=='unpaved','10_emission'] = gdf_filtered.loc[gdf_filtered['surface']=='unpaved','flow'] * gdf_filtered.loc[gdf_filtered['surface']=='unpaved','length']/1000 * gdf_filtered.loc[gdf_filtered['surface']=='unpaved','EF10_corrected'] / 3600


### PM30
#Fator de emissão PM30 em lb/VMT
gdf_filtered.loc[gdf_filtered['surface']=='unpaved','EF30'] = ef.emission_unpaved_public(30, gdf_filtered.loc[:,'silt_fraction'], (gdf_filtered.loc[:,'traffic_level'] * 0.621371), gdf_filtered.loc[:,'soil_moisture'])

    #0.621371 é o fator de conversão de km/h para mph

#Conversão de lb/VMT para g/VKT
gdf_filtered.loc[gdf_filtered['surface']=='unpaved','EF30'] = gdf_filtered.loc[:,'EF30'].apply(ef.lbvmt_to_gvkt)

#Correção da emissão pela pluviosidade
gdf_filtered.loc[gdf_filtered['surface']=='unpaved','EF30_corrected'] = ef.unpaved_rainfall_correction(gdf_filtered['EF30'], 100, 365)

#Taxa de Emissão de Pm30 por trecho de via (g/s)
gdf_filtered.loc[gdf_filtered['surface']=='unpaved','30_emission'] = gdf_filtered.loc[gdf_filtered['surface']=='unpaved','flow'] * gdf_filtered.loc[gdf_filtered['surface']=='unpaved','length']/1000 * gdf_filtered.loc[gdf_filtered['surface']=='unpaved','EF30_corrected'] / 3600 

#%% EMISSÕES VIAS PAVIMENTADAS

# Dados iniciais
weight = 2.4 

### PM2.5
#Fator de emissão PM2.5 em g/VKT
gdf_filtered.loc[gdf_filtered['surface']=='paved','EF25'] = ef.emission_paved_roads(2.5, gdf_filtered.loc[:,'silt_loading'], weight)

#Correção da emissão pela pluviosidade
gdf_filtered.loc[gdf_filtered['surface']=='paved','EF25_corrected'] = ef.paved_rainfall_correction(gdf_filtered['EF25'], 100, 365)

#Taxa de emissão de Pm2.5 por trecho de via (g/s)
gdf_filtered.loc[gdf_filtered['surface']=='paved','25_emission'] = gdf_filtered.loc[gdf_filtered['surface']=='paved','flow'] * gdf_filtered.loc[gdf_filtered['surface']=='paved','length']/1000 * gdf_filtered.loc[gdf_filtered['surface']=='paved','EF25_corrected'] / 3600


### PM10
#Fator de emissão PM10 em g/VKT
gdf_filtered.loc[gdf_filtered['surface']=='paved','EF10'] = ef.emission_paved_roads(10, gdf_filtered.loc[:,'silt_loading'], weight)

#Correção da emissão pela pluviosidade
gdf_filtered.loc[gdf_filtered['surface']=='paved','EF10_corrected'] = ef.paved_rainfall_correction(gdf_filtered['EF10'], 100, 365)

#Taxa de emissão de Pm10 por trecho de via (g/s)
gdf_filtered.loc[gdf_filtered['surface']=='paved','10_emission'] = gdf_filtered.loc[gdf_filtered['surface']=='paved','flow'] * gdf_filtered.loc[gdf_filtered['surface']=='paved','length']/1000 * gdf_filtered.loc[gdf_filtered['surface']=='paved','EF10_corrected'] / 3600


### PM30
#Fator de emissão PM30 em g/VKT
gdf_filtered.loc[gdf_filtered['surface']=='paved','EF30'] = ef.emission_paved_roads(30, gdf_filtered.loc[:,'silt_loading'], weight)

#Correção da emissão pela pluviosidade
gdf_filtered.loc[gdf_filtered['surface']=='paved','EF30_corrected'] = ef.paved_rainfall_correction(gdf_filtered['EF30'], 100, 365)

#Taxa de Emissão de Pm30 por trecho de via (g/s)
gdf_filtered.loc[gdf_filtered['surface']=='paved','30_emission'] = gdf_filtered.loc[gdf_filtered['surface']=='paved','flow'] * gdf_filtered.loc[gdf_filtered['surface']=='paved','length']/1000 * gdf_filtered.loc[gdf_filtered['surface']=='paved','EF30_corrected'] / 3600

