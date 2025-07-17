#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 16 15:13:05 2025

@author: brunojalowski
"""
import geopandas as gpd
import pandas as pd

def drop_duplicates_from_combination(data: pd.DataFrame | gpd.GeoDataFrame,
                                     column1: str,
                                     column2: str) -> (gpd.GeoDataFrame |
                                                       pd.DataFrame):
    """
    Removes duplicate values based on a combination of two columns.
    
    Parameters
    ----------
    data: pd.DataFrame | gpd.GeoDataFrame
        DataFrame or GeoDataFrame with duplicate values.
    column1 : str
        Second column.
    column2 : str
        Second column.
    
    Returns
    -------
    gpd.GeoDataFrame | pd.DataFrame
        Geodataframe or Dataframe without duplicate values.

    Example:
    --------
               person1 person2 messages
        0   0   ryan    delta   1
        1   1   delta   ryan    1
        2   2   delta   alpha   2
        3   3   delta   bravo   3
        4   4   bravo   delta   3
        5   5   alpha   ryan    9
        6   6   ryan    alpha   9
        
                person1 person2 messages
        0   0   ryan    delta   1
        1   2   delta   alpha   2
        2   3   delta   bravo   3
        3   5   alpha   ryan    9
    
    
    Source: https://stackoverflow.com/questions/74707663/remove-duplicates-
    based-on-combination-of-two-columns-in-pandas

    """
    # Creating boolean list where value from column1 is smaller than column2
    swap = data[column1] < data[column2]
    
    # Standardizing all duplicate columns
    data.loc[swap, [column1, column2]] = (
        data.loc[swap, [column2, column1]].values
        )

    # Dropping duplicate geometries
    data = data.drop_duplicates(subset=[column1, column2])
    
    return data
    
    