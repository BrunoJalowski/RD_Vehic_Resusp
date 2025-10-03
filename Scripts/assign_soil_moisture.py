#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Oct  3 08:59:29 2025

@author: brunojalowski
"""
import geopandas as gpd
from shapely import LineString
import numpy as np

def assign_soil_moisture(line: LineString,
                            grid: gpd.GeoDataFrame) -> float:
    """
    Calculates the average soil moisture value for each road segment weighted
    by the length inside each pixel.

    Parameters
    ----------
    line : LineString
        ROAD SEGMENT FROM ROAD VECTOR DATAFRAME.
    grid : gpd.GeoDataFrame
        VECTOR GRID MADE FROM VECTORIZING RASTER/XARRAY.

    Returns
    -------
    float
        WEIGHTED AVERAGE FOR SOIL MOISTURE.

    """
    
    # Selects only cells that intersect with the linestring
    intersected_cells = grid[grid.intersects(line)].copy()
    if intersected_cells.empty:
        return np.nan
    
    # Gets line total length
    intersected_cells["total_length"] = (line
                                         .length)
    
    # Gets length of line inside each cell
    intersected_cells["intersected_length"] = (intersected_cells
                                               .geometry
                                               .intersection(line)
                                               .length)
    
    # Weight factor
    intersected_cells["weight_factor"] = (
        intersected_cells["intersected_length"] /
        intersected_cells["total_length"]
        )
    
    # Soil moisture weighted average
    weighted_average = (
        intersected_cells['weight_factor'] *
        intersected_cells['value']
        ).sum()
    
    return weighted_average