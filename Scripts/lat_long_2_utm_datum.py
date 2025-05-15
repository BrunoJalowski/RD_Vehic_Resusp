#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May 13 18:19:16 2025

@author: brunojalowski
"""
import numpy as np

def lat_long_2_sirgas_utm(lat,long):
    zone = (np.floor((long + 180)/6) % 60) + 1
    hemi_code = 'EPSG:319'
    
    if lat > 0:
        zone_code = str(60 + zone)
        return hemi_code + zone_code
    
    else:
        zone_code = str(54 + zone)
        return hemi_code + zone_code
    
     #FIXME VETORIZAR O IF ELSE DA FUNÇÃO PARA SER APLICADA NA COLUNA TODA