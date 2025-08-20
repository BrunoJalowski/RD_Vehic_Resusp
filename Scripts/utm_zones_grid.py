#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Aug 19 14:29:35 2025

@author: brunojalowski
"""
import numpy as np
import shapely
import geopandas as gpd

class UtmZoneGrid:
    def __init__(self, zone, hemisphere):
        self.zone = int(zone)
        self.hemisphere = hemisphere
        self.__get_epsg_code()
        self.__get_zone_bounds()
        self.__create_vector_grid()
        self.bounds = (self.west_bound, self.south_bound, 
                       self.east_bound, self.north_bound)
    
    def __get_epsg_code(self):
        epsg_south = 'EPSG:319' + str(int(60 + self.zone))
        epsg_north = 'EPSG:319' + str(int(54 + self.zone))

        self.epsg_code = np.where(self.hemisphere == 'N', 
                                  epsg_north,
                                  epsg_south)
    
    def __get_zone_bounds(self):
        self.east_bound = (self.zone * 6) - 180
        self.west_bound = self.east_bound - 6
        self.north_bound = np.where(self.hemisphere == 'N', 90, 0).astype(int)
        self.south_bound = np.where(self.hemisphere == 'N', 0, 90).astype(int)
        
    def __create_vector_grid(self):
        boundbox = shapely.box(self.west_bound, self.south_bound, 
                               self.east_bound, self.north_bound)
        self.polygon_grid = gpd.GeoSeries(boundbox)
        
        self.linestring_grid = self.polygon_grid.boundary
    
    
    
#%%
zone25_grid = UtmZoneGrid(25, 'N')

utm_zones_BR = 