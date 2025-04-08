#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr  8 17:18:46 2025

@author: brunojalowski
"""
from emissions import gdf_filtered
import rasterio
from rasterio.enums import MergeAlg
import matplotlib.pyplot as plt
#%%

# CMIP data shape = 257,247]

#%%

fig, ax = plt.subplots(figsize=(10, 10))
xr.plot.pcolormesh(darray=['band_1'],ax=ax, alpha=0.5)