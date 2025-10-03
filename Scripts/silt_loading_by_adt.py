#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Oct  2 18:05:23 2025

@author: brunojalowski
"""

def silt_loading_by_adt(gdf):
    '''

    Returns
    -------
    None.
    
    """ Silt loading according to Average Daily Traffic (ADT) values from AP-42:
            0 < ADT <   500 --> 0.6
          500 < ADT <  5000 --> 0.2
         5000 < ADT < 10000 --> 0.06
        10000 < ADT < infinity --> 0.03
    """
    
    '''
    
    
    adt = gdf['average_daily_vehicle_count']
    
    # Assigning silt loading values by ADT
    gdf.loc[(gdf['silt_loading'].isna()) &
            (adt < 500) &
            (gdf['surface'] == 'paved'),'silt_loading'] = 0.6

    gdf.loc[(gdf['silt_loading'].isna()) &
            (adt >= 500) &
            (adt < 5000) &
            (gdf['surface'] == 'paved'),'silt_loading'] = 0.3

    gdf.loc[(gdf['silt_loading'].isna()) &
            (adt >= 5000) &
            (adt < 10000) &
            (gdf['surface'] == 'paved'),'silt_loading'] = 0.06

    gdf.loc[(gdf['silt_loading'].isna()) &
            (adt >= 10000) &
            (gdf['surface'] == 'paved'),'silt_loading'] = 0.03
    
    return gdf