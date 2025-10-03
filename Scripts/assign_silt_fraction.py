#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Oct  3 09:01:39 2025

@author: brunojalowski
"""
import numpy as np

def assign_silt_fraction(gdf, raster):
    """
    Assigns silt fraction values for each point of each linestring

    Parameters
    ----------
    gdf : TYPE
        DESCRIPTION.
    raster : TYPE
        DESCRIPTION.

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
            """For each LineString, rIndustrial_Sites import roads_template as 
            gdfeturns the closest indexes and with them, the silt fraction values"""
            for point in line.coords:
                lon, lat = point
                lat_idx = np.abs(raster['y'] - lat).argmin()  
                lon_idx = np.abs(raster['x'] - lon).argmin()  
                value = raster['band_1'].values[lat_idx, lon_idx]  
                line_values.append(value)
            values.append(line_values)  
    
        else:
            values.append(None)  
    
    
    gdf['silt_fraction'] = values
    gdf.loc[:,'silt_fraction'] = gdf.loc[:,'silt_fraction'].str[0]
    
    del lat, lat_idx, line, line_values,lon,lon_idx,point,row
    
    return gdf