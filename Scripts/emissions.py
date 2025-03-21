#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar 21 11:46:24 2025

@author: brunojalowski
"""
import xarray as xr
import matplotlib.pyplot as plt
import netcdf4_conversions_v2 as conv
import numpy as np
from main import gdf_filtered
import emission_factors as ef

#%%Dados iniciais via não pavimentada
silt_fraction = 1
pm = 2.5    # 


#%%Fator de emissão PM2.5 por trecho de via não pavimentada de acesso público em lb/VMT
gdf_filtered.loc[gdf_filtered['surface']=='unpaved','EF_unpaved'] = ef.emission_unpaved_public(pm, silt_fraction, (gdf_filtered.loc[:,'traffic_level'] * 0.621371), gdf_filtered.loc[:,'soil_moisture'])

# 0.621371 é o fator de conversão de km/h para mph

#%%Conversão de lb/VMT para g/VKT
gdf_filtered.loc[gdf_filtered['surface']=='unpaved','EF_unpaved'] = gdf_filtered.loc[:,'EF_unpaved'].apply(ef.lbvmt_to_gvkt)

#%%Correção da emissão pela pluviosidade
gdf_filtered.loc[gdf_filtered['surface']=='unpaved','EF_unpaved_corrected'] = ef.paved_rainfall_correction(gdf_filtered['EF_unpaved'], 100, 365)

#%%Emissão de Pm2.5 por trecho de via
gdf_filtered.loc[gdf_filtered['surface']=='unpaved','emission'] = gdf_filtered.loc[gdf_filtered['surface']=='unpaved','flow'] * gdf_filtered.loc[gdf_filtered['surface']=='unpaved','length']/1000 * gdf_filtered.loc[gdf_filtered['surface']=='unpaved','EF_unpaved_corrected'] 


#%%Mostrar a distribuição das emissões no espaço









