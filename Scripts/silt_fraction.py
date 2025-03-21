#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar 21 11:34:11 2025

@author: brunojalowski
"""

import rasterio

#%%

silt_fraction = rasterio.open('/home/brunojalowski/Documentos/RD_Vehic_Resusp/dados_entrada/MAPBIOMAS-EXPORT-20250220T123349Z-001/MAPBIOMAS-EXPORT/mapbiomas-brazil-collection-beta-2021-cos_0_30cm_kg_m2-0000000000-0000158720.tif', mode='r')

band1 = silt_fraction.read(1)







    

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

#%%
with rasterio.open('/home/brunojalowski/Documentos/RD_Vehic_Resusp/dados_entrada/MAPBIOMAS-EXPORT-20250220T123349Z-001/MAPBIOMAS-EXPORT/mapbiomas-brazil-collection-beta-2021-cos_0_30cm_kg_m2-0000126976-0000000000.tif') as src:
    # Verifique os metadados
    print(f"Driver: {src.driver}")
    print(f"Formato de dados: {src.dtypes[0]}")
    print(f"Resolucao espacial: {src.res}")
    print(f"CRS: {src.crs}")
    print(f"Numero de bandas: {src.count}")
    print(f"Valor NoData: {src.nodata}")
      
    band = src.read(1)  # Lê a primeira banda
    print(band.min(), band.max())  # Verifica os valores mínimo e máximo da banda
    
    
    
    
    
    
    
    