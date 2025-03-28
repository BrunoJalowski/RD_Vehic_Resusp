#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar 21 11:34:11 2025

@author: brunojalowski

DATASET SOURCE: https://brasil.mapbiomas.org/metodo-mapbiomas-solo/


"""
import os
import rasterio
import rioxarray as rxr
import glob
from pathlib import Path
from rioxarray.merge import merge_arrays

#%% PATH
project_path = Path('/home/brunojalowski/Documentos/RD_Vehic_Resusp/dados_entrada')
silt_fraction_path = project_path /'MAPBIOMAS-EXPORT-20250220T123349Z-001/MAPBIOMAS-EXPORT'

#%%
os.environ["GDAL_DISABLE_READDIR_ON_OPEN"] = "TRUE"
#%%
files = glob.glob(str(silt_fraction_path / '*.tif'))
open_files = [rxr.open_rasterio(tif) for tif in files]

#%%
merged = rxr.merge.merge_arrays(open_files)


   