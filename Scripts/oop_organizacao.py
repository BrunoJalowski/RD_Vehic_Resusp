#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Aug 13 17:46:16 2025

@author: brunojalowski
"""
import geopandas as gpd
from pathlib import Path
from shapely.geometry import box, LineString
import numpy as np
import xarray as xr
import netcdf4_conversions_v2 as conv
from trafficdata.utils.geometries import split_lines_vectorized

#%% Paths
#project_path = Path('/home/brunojalowski/Documentos/RD_Vehic_Resusp/dados_entrada')
project_path = Path(r"C:\Users\bruno\Desktop\LCQAr\RD_Vehic_Resusp\dados_entrada")

soil_moisture_path = (project_path /
                      r'Soil Moisture/METCRO2D_BR_20km_2023-02-01.nc')
silt_fraction_path = (project_path /
                      'Silt_Fraction')
flow_path = (project_path /
             'vehicle_count_daily-2025-07-09 00_00_00_to_2025-07-10 00_00_00'
             '_rev1.parquet')

fleet_path = Path(r'/home/brunojalowski/Documentos/RD_Vehic_Resusp/dados_entrada/'
              'FrotapormunicipioetipoDezembro2024.xlsx')


#%%
def length_weighted_avg(line: LineString,
                         grid: gpd.GeoDataFrame) -> float:
    """
    Calculates the average value for each linestring segment weighted
    by the length inside each grid cell.

    Parameters
    ----------
    line : LineString
        LINESTIRNG FROM ROAD VECTOR DATAFRAME.
    grid : gpd.GeoDataFrame
        VECTOR GRID MADE FROM VECTORIZING RASTER/XARRAY.

    Returns
    -------
    float
        WEIGHTED AVERAGE.

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



#%%

class RoadDataset:
    def __init__(self, flow_path):
        self.dataframe = (gpd
                          .read_parquet(path=flow_path)
                          .astype({'osm_id': int,
                                   'vehicle_count': float,
                                   'average_daily_vehicle_count': float,
                                   'road_length': float,
                                   'vkt_per_hour': float,
                                   'surface': str,
                                   'avg_traffic_level': float})
                          .reset_index(drop=False)
                          )


class RessuspensionModel:
    def __init__(self):
        
        self.__classify_pavement()
        self.__assign_soil_moisture(soil_moisture_grid)
        
        
    def __classify_pavement(self):
        self.dataframe.loc[(self.dataframe['surface'] == 'asphalt') |
                           (self.dataframe['surface'] == 'paving_stones') |
                           (self.dataframe['surface'] == 'sett') |
                           (self.dataframe['surface'] == 'cobblestone') |
                           (self.dataframe['surface'] == 'metal') |
                           (self.dataframe['surface'] == 'concrete:plates'),
                           'surface'] = 'paved'

        self.dataframe.loc[(self.dataframe['surface'] == 'compacted') |
                           (self.dataframe['surface'] == 'None') |
                           (self.dataframe['surface'] is None) |
                           (self.dataframe['surface'] == 'ground') |
                           (self.dataframe['surface'] == 'gravel') |
                           (self.dataframe['surface'] == 'dirt'), 'surface'] = 'unpaved'
    
    
    def __assign_soil_moisture(self, soil_moisture_grid):
        values = []
        for ii in range(self.dataframe.shape[0]):
                line = self.dataframe.geometry.iloc[ii]
                value = length_weighted_avg(line, soil_moisture_grid)
                if value > 0 :
                    values.append(value)
                else:
                    values.append(None)

        self.dataframe['soil_moisture'] = values
        del value, values, ii
    
    
    def split_by_line(self, line_df):
        self.dataframe = split_lines_vectorized(self,
                                                line_df.explode())
        
        
        
    
class NetCDF:
    def __init__(self, file_path, variable):
        self.dataset = xr.open_mfdataset(file_path, engine='netcdf4')
        self.dataset = conv.brain_to_latlng(self.dataset)
        self.dataset = self.dataset[str(variable)]
        self.__create_vector_grid()
    
    def __create_vector_grid(self):
        # Pixels' centroids from soil_moisture
        lons = self.dataset['lon'].values
        lats = self.dataset['lat'].values

        # Calculates halfways between centroids
        lon_edges = np.concatenate([
            [lons[0] - (lons[1] - lons[0]) / 2],
            (lons[:-1] + lons[1:]) / 2,
            [lons[-1] + (lons[-1] - lons[-2]) / 2]
        ])

        lat_edges = np.concatenate([
            [lats[0] - (lats[1] - lats[0]) / 2],
            (lats[:-1] + lats[1:]) / 2,
            [lats[-1] + (lats[-1] - lats[-2]) / 2]
        ])

        # Creates grid cells based on the edges coordinates
        grid_cells = []
        i_indexes = []
        j_indexes = []
        for i in range(len(lat_edges) - 1):
            for j in range(len(lon_edges) - 1):
                cell = box(
                    lon_edges[j],
                    lat_edges[i],
                    lon_edges[j + 1],
                    lat_edges[i + 1]
                )
                grid_cells.append(cell)
                i_indexes.append(i)
                j_indexes.append(j)

        del i, j, cell

        # Turns it into a GeoDataFrame
        self.grid = gpd.GeoDataFrame(geometry=grid_cells, crs="EPSG:4326")
        self.grid['i_index'] = i_indexes
        self.grid['j_index'] = j_indexes

        # Deleting variables
        del i_indexes, j_indexes

        # Get the soil moisture values as a 2D array
        values = self.dataset.isel(TSTEP=0,LAY=0).values

        # Map the values to the grid cells
        self.grid['value'] = [values[i, j] 
                              for i, j 
                              in zip(self.grid['i_index'], 
                                     self.grid['j_index'])
                              ]

        # Drop the indices
        self.grid = self.grid.drop(columns=['i_index', 'j_index'])
    


# %%
# Creating road geodataframe
gdf = RoadDataset(flow_path)

# Reclassifying roads in paved or unpaved
gdf.classify_pavement()

#



# Creating soil moisture dataset
soil_moisture_dataarray = NetCDF(soil_moisture_path, "SOIM1")

# Creating aoil moisture vector grid
soil_moisture_dataarray.create_vector_grid()

# Assigning soil moisture values to each road segment
gdf.assign_soil_moisture(soil_moisture_dataarray.grid)

# 

