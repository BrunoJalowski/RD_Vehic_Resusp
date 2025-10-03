#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul  8 12:30:38 2025

@author: brunojalowski
"""
# %% Road surface reclassification

def reclassify_surface(gdf):
    """
    

    Parameters
    ----------
    gdf : TYPE
        DESCRIPTION.

    Returns
    -------
    gdf : TYPE
        DESCRIPTION.

      
    Classificação atual:
        array(['asphalt', 'paving_stones', 'compacted', None, 'unpaved', 'sett',
           'paved', 'cobblestone', 'metal', 'ground', 'gravel', 'dirt',
           'concrete:plates'], dtype=object)

    Reclassificação:
        paved = asphalt, paving_stones,sett, paved, cobblestone, metal,
                concrete:plates
        unpaved = compacted, None, unpaved, ground, gravel, dirt
        
    """
    paved = ['asphalt', 'paving_stones', 'sett', 'paved', 'cobblestone',
             'metal', 'concrete:plates']
    
    unpaved = ['compacted', 'unpaved', 'None', 'ground', 'gravel', 'dirt']
       
    gdf.loc[gdf['surface'].isin(paved), 'surface'] = 'paved'

    gdf.loc[(gdf['surface'].isin(unpaved)) |
            (gdf['surface'].isnull()), 'surface'] = 'unpaved'
    
    return gdf
    
    


