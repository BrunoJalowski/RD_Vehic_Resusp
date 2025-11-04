#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Oct  3 09:01:39 2025

@author: brunojalowski
"""
import numpy as np
import geopandas as gpd
import xarray as xr

def assign_silt_fraction(gdf: gpd.GeoDataFrame, 
                         raster:xr.DataArray,
                         band:int = 1):
    """
    Assigns silt fraction values for each point of each linestring and 
    returns the simple average for each road.
    
    Example: A road made up of 5 segments is compared with the raster cells
    and gets assigned the values 10, 20, 30, 40, 50. For this road, the
    resulting silt fraction will be (10+20+30+40+50)/5 = 30

    Parameters
    ----------
    gdf : gpd.GeoDataFrame
        Vector of roads with exclusively LineString geometries.
    raster : xr.DataArray
        Raster dataset with a 'band' dimension.
    band : int, optional
        Band dimension of raster in which are the wanted values. 
        The default is 1.

    Returns
    -------
    gdf : TYPE
        DESCRIPTION.

    """
    #Designando valores de teor de silte para cada trecho de via
    values = []
    for _, row in gdf.iterrows():
        line = row['geometry']  
    
        if line.geom_type == 'LineString':
            line_values = []  
            """For each LineString, returns the closest indexes and with them,
            the silt fraction values"""
            for point in line.coords:
                lon, lat = point
                lat_idx = np.abs(raster['y'] - lat).argmin()  
                lon_idx = np.abs(raster['x'] - lon).argmin()  
                value = raster.sel(band=band).values[lat_idx, lon_idx]  
                line_values.append(value)
            values.append(line_values)  
    
        else:
            values.append(None)  
    
    
    gdf['silt_fraction'] = values
    gdf.loc[:,'silt_fraction'] = (gdf.loc[:,'silt_fraction']
                                  .apply(np.asarray)
                                  .apply(np.mean))
    
    del lat, lat_idx, line, line_values,lon,lon_idx,point,row
    
    return gdf

