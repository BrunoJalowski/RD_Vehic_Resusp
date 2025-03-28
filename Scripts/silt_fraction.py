#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar 21 11:34:11 2025

@author: brunojalowski
"""

from rasterio.enums import Resampling
from rasterio.crs import CRS
import matplotlib.pyplot as plt
import rioxarray as rxr
    
#%%
# Opening raster
silt_fraction = rxr.open_rasterio('/home/brunojalowski/Documentos/RD_Vehic_Resusp/dados_entrada/MAPBIOMAS-EXPORT-20250220T123349Z-001/MAPBIOMAS-EXPORT/mapbiomas-brazil-collection-beta-2021-cos_0_30cm_kg_m2-0000000000-0000158720.tif')

#%%
# Setting downscale factor
downscale_factor = 1/5

# new height and width
new_width = silt_fraction.rio.width * downscale_factor
new_height = silt_fraction.rio.height * downscale_factor

# Correcting scale_factor attribute
silt_fraction.attrs['scale_factor'] = 0.2

# Downscaling
silt_fraction = silt_fraction.rio.reproject(silt_fraction.rio.crs, shape=(int(new_height),
                                                     int(new_width)),
                                            resampling=Resampling.bilinear)

silt_fraction= silt_fraction.where(silt_fraction > 0)

#%%


#%% Opening raster data 

with rasterio.open('/home/brunojalowski/Documentos/RD_Vehic_Resusp/dados_entrada/MAPBIOMAS-EXPORT-20250220T123349Z-001/MAPBIOMAS-EXPORT/mapbiomas-brazil-collection-beta-2021-cos_0_30cm_kg_m2-0000000000-0000158720.tif', mode='r') as src:
    # Verifique os metadados da imagem
    print(f"Formato do arquivo: {src.driver}")
    print(f"Tipo de dado: {src.dtypes[0]}")
    print(f"Formato de dados: {src.count} banda(s)")
    print(f"Resolução espacial: {src.res}")
    print(f"Tamanho da imagem: {src.width} x {src.height}")
    print(f"Valor NoData: {src.nodata}")
    
    # Verifique o range de valores da imagem
    img = src.read(1).astype('int16')  # Ler a primeira banda
    print(f"Min valor: {img.min()}, Max valor: {img.max()}")


"""
Formato do arquivo: GTiff
Tipo de dado: int16
Formato de dados: 1 banda(s)
Resolução espacial: (0.00026949458523585647, 0.00026949458523585647)
Tamanho da imagem: 8790 x 31744
Valor NoData: None
Min valor: 0, Max valor: 0"""

    