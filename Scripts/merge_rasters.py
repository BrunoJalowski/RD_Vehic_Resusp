#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct 14 13:53:01 2025

@author: brunojalowski
"""
import glob
import rioxarray as rxr
from rioxarray.merge import merge_arrays
from pathlib import Path

#%%
inputs_path = Path('../inputs').resolve()

silt_fraction_path = inputs_path / 'Silt_Fraction'

#%% SETTING UP SILT FRACTION RASTER
# Opening file
files = glob.glob(str(silt_fraction_path / '*.tif'))

raster_list = [rxr.open_rasterio(file) for file in files]

# Merge/Mosaic multiple rasters using merge_arrays method of rioxarray
merged_raster = merge_arrays(dataarrays = raster_list,
                             crs="EPSG:4326",
                             nodata = 0)
 
# Save Raster to disk
merged_raster.rio.to_raster(silt_fraction_path / "merged_rasters.tif",
                            driver="GTiff",
                            compress="DEFLATE",
                            num_threads="ALL_CPUS")
