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
import pandas as pd
import glob
from long_2_utm_zone import long_2_utm_zone
from utm_zone_2_epsg import utm_zone_2_epsg
import time

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

industrial_path = project_path /'Industrias'
mining_path = industrial_path / 'MiningBR/BRASIL_FILTRADO.shp'
cnpj_path = industrial_path / 'PessoasJuridicas'
landfills_path = (industrial_path / 'SINISA_RESIDUOS_Planilhas_2023/'
                  'SINISA_RESIDUOS_Informacoes_Formulario_Infraestrutura'
                  '_Destinacao_Final_2023.xlsx')

#%% FUNCTIONS
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
        self.geodataframe = (gpd
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


    
        
        
    
class PixeledData:
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
    
    
class EnterprisesDataset:
    def __init__(self, cnpj_path):
        # Reading and merging industries datasets
        files = glob.glob(str(cnpj_path / '*.csv'))
        self.geodataframe = pd.read_csv(files[0], sep='\t', skiprows=2)

        for file in files[1:]:
            opened = pd.read_csv(file, sep='\t', skiprows=2)
            self.geodataframe = pd.merge(self.geodataframe, opened, how='outer')
        
        # Replacing commas with dots in the coordinates
        self.geodataframe.Latitude = (self.geodataframe['Latitude']
                            .str.replace(',', '.', regex=False)
                            .astype(float))
        self.geodataframe.Longitude = (self.geodataframe['Longitude']
                             .str.replace(',', '.', regex=False)
                             .astype(float))
    
        """Filtrando:
            - Atividade industriais presentes na tabela de Default Silt 
            Loading da AP42:
                3.1: Fabricação de aço e de produtos siderúrgicos
                3.2: Produção de fundidos de ferro e aço, forjados, arames, 
                relaminados com ou sem tratamento de superfície, inclusive 
                galvanoplastia
                3.11: Têmpera e cementação de aço, ecozimento de arames e 
                tratamento de superfície
                14.1: Produção de Cimento
                14.2: Produção de Concreto
                16.1: Beneficiamento, moagem, torrefação e fabricação de 
                produtos alimentares
            - Em situação cadastral ativa
            """
        self.geodataframe = self.geodataframe.loc[(
            (self.geodataframe['Código da categoria'] == 3) &
            (self.geodataframe['Situação cadastral'] == 'Ativa') &
            (self.geodataframe['Código da atividade'].isin([1, 2, 11]))
            ) |
            ((self.geodataframe['Código da categoria'] == 14) &
             (self.geodataframe['Situação cadastral'] == 'Ativa') &
             (self.geodataframe['Código da atividade'].isin([1, 2]))
            ) |
            ((self.geodataframe['Código da categoria'] == 16) &
             (self.geodataframe['Situação cadastral'] == 'Ativa') &
             (self.geodataframe['Código da atividade'] == 1)
            ), :]
        
        # Creating Geodataframe
        self.geodataframe = (
            gpd.GeoDataFrame(self.geodataframe,
                             geometry=gpd.points_from_xy(
                                 self.geodataframe.Longitude,
                                 self.geodataframe.Latitude,
                                 crs='EPSG:4326')))
        
        # Creating column with UTM zone for each point
        self.geodataframe['EPSG'] = long_2_utm_zone(self.geodataframe['Longitude'])

        # Removing points outside of Brazil
        self.geodataframe.dropna(inplace=True)
        self.geodataframe = (self.geodataframe
                             .loc[(self.geodataframe['Longitude'] != 0) |
                                  (self.geodataframe['Latitude'] != 0)])

        # Creating column with EPSG code
        self.geodataframe['EPSG'] = utm_zone_2_epsg(self.geodataframe['EPSG'],
                                                    self.geodataframe['Latitude'])


class LandfillSitesDataset:
    def __init__(self, landfills_path):
        self.dataframe = pd.read_excel(landfills_path,
                                       engine='openpyxl',
                                       skiprows=12)
        
        self.dataframe = self.dataframe.loc[(~pd.isna(self.dataframe['GTR3203*']) &
                                             ~pd.isna(self.dataframe['GTR3204*'])),
                                            ['CAD1000 ','GTR3202*','GTR3203*','GTR3204*']]

        # Formatting coordinates
        self.dataframe.loc[:, 'GTR3203*'] = (self.dataframe
                                              .loc[:, 'GTR3203*']
                                              .str.split()
                                              .str[-1])

        self.dataframe.loc[:, 'GTR3204*'] = (self.dataframe
                                              .loc[:, 'GTR3204*']
                                              .str.split()
                                              .str[-1])

        # Turning coordinates to float
        self.dataframe.loc[:, 'GTR3203*'] = (self.dataframe
                                             .loc[:, 'GTR3203*']
                                             .astype(float))
        
        self.dataframe.loc[:, 'GTR3204*'] = (self.dataframe
                                              .loc[:, 'GTR3204*']
                                              .astype(float))

        # Renaming columns
        self.dataframe = self.dataframe.rename(columns={'CAD1000 ':'CNPJ',
                                                          'GTR3203*':'Latitude',
                                                          'GTR3204*':'Longitude',
                                                          'GTR3202*':'Nome'})

        # Creating geodataframe from lon and lat columns
        self.dataframe = (
            gpd.GeoDataFrame(self.dataframe,
                             geometry = gpd.points_from_xy(self.dataframe.Longitude,
                                                           self.dataframe.Latitude),
                             crs="EPSG:4326")
            )
        # Resetting index
        self.dataframe = self.dataframe.reset_index(drop=True)
        
        # Getting utm zone using the longitude
        self.dataframe.loc[:,'utm_zone'] = long_2_utm_zone(self.dataframe['Longitude']) 

        # Assigning EPSG SIRGAS 2000 code according to UTM zone and latitude
        self.dataframe.loc[:,'EPSG'] = utm_zone_2_epsg(self.dataframe['utm_zone'],
                                                     self.dataframe['Latitude'])

        self.dataframe.drop(columns='utm_zone', inplace=True)
        
        # Assigning default silt loading value for landfill activity
        self.dataframe['silt_loading'] = 7.4
        
        
class MiningSitesDataset:
    def __init__(self, mining_path):
        self.geodataframe = gpd.read_file(mining_path, engine='fiona')
        # Getting UTM zone from Longitude
        self.geodataframe.loc[:,'utm_zone'] = long_2_utm_zone(self.geodataframe
                                                              .geometry
                                                              .centroid
                                                              .x) 
    
        # Atribuindo código EPSG SIRGAS 2000 projetado de acordo com a zona 
        # UTM e a latitude
        self.geodataframe.loc[:,'EPSG'] = utm_zone_2_epsg(self.geodataframe['utm_zone'],
                                                          self.geodataframe.geometry
                                                          .centroid
                                                          .x)
    
        self.geodataframe.drop(columns='utm_zone', inplace=True)
        
        # Assigning default silt loading value for mining sites under Quarry
        # class from AP42
        self.geodataframe['silt_loading'] = 8.2


class IndustrialSitesDataset:
    def __init__(self, industrial_activities_list):
       self.geodataframe = pd.concat(industrial_activities_list).reset_index()
       
       self.geodataframe.loc[~pd.isna(self.geodataframe['Nome']),
                          'Razão Social'] = self.geodataframe['Nome']
       self.geodataframe.loc[~pd.isna(self.geodataframe['NOME']),
                          'Razão Social'] = self.geodataframe['NOME']

       self.geodataframe.drop(columns=['Nome', 'NOME'], inplace=True)

       # Creating identifier column for each industrial site
       self.geodataframe['activity_id'] = self.geodataframe.index

       # Creating buffers
       
       choices = {'{}'.format(q): q for q in self.geodataframe['EPSG'].unique()}
       
       for epsg in choices.keys():
           
            # Creating sub dataframe and setting respective crs
            choices[epsg] = (
                self.geodataframe[self.geodataframe['EPSG'] == epsg]
                .to_crs(epsg)
                )
            
            # Creating buffers in km and converting to WGS 84
            choices[epsg]['buffer_ind'] = choices[epsg].buffer(500).to_crs(4326)
            choices[epsg]['buffer_amort'] = choices[epsg].buffer(600).to_crs(4326)
            
            # Reprojecting geometry of each sub dataframe to WGS 84
            choices[epsg] = choices[epsg].to_crs(4326)
        
       self.geodataframe = gpd.GeoDataFrame(pd.concat([choices[df]
                                                       for df
                                                       in choices])) 
       
       # 500 m radius buffer
       self.buffer_ind = gpd.GeoDataFrame(
           data=self.geodataframe[['activity_id','silt_loading']],
           geometry=self.geodataframe['buffer_ind']
           )
       
       # 600 m radius buffer
       self.buffer_amort = gpd.GeoDataFrame(
           data=self.geodataframe[['activity_id','silt_loading']],
           geometry=self.geodataframe['buffer_amort']
           )

       """Transition values in buffer_amort are an average between industrial 
       and the upper limit of AP-42 default silt loading, 0.6 g/m²"""
       self.buffer_amort['silt_loading'] = (
           (self.buffer_amort['silt_loading'] + 0.6) / 2
           )
       
       
       
       
class RessuspensionModel:
    def __init__(self):
        self.__classify_pavement()
        self.__split_by_line()
        self.__assign_soil_moisture(soil_moisture_grid)
        
    def __classify_pavement(self):
        self.geodataframe.loc[(self.geodataframe['surface'] == 'asphalt') |
                           (self.geodataframe['surface'] == 'paving_stones') |
                           (self.geodataframe['surface'] == 'sett') |
                           (self.geodataframe['surface'] == 'cobblestone') |
                           (self.geodataframe['surface'] == 'metal') |
                           (self.geodataframe['surface'] == 'concrete:plates'),
                           'surface'] = 'paved'

        self.geodataframe.loc[(self.geodataframe['surface'] == 'compacted') |
                           (self.geodataframe['surface'] == 'None') |
                           (self.geodataframe['surface'] is None) |
                           (self.geodataframe['surface'] == 'ground') |
                           (self.geodataframe['surface'] == 'gravel') |
                           (self.geodataframe['surface'] == 'dirt'), 'surface'] = 'unpaved'
    
    
    def __assign_soil_moisture(self, soil_moisture_grid):
        values = []
        for ii in range(self.geodataframe.shape[0]):
                line = self.geodataframe.geometry.iloc[ii]
                value = length_weighted_avg(line, soil_moisture_grid)
                if value > 0 :
                    values.append(value)
                else:
                    values.append(None)

        self.geodataframe['soil_moisture'] = values
        del value, values, ii
    
    
    def split_by_line(self, line_df):
        self.geodataframe = split_lines_vectorized(self,
                                                line_df.explode())
       
# %%
# Creating road geodataframe
gdf = RoadDataset(flow_path)

# Reclassifying roads in paved or unpaved
gdf.classify_pavement()

# 



# Creating soil moisture dataset
soil_moisture_dataarray = PixeledData(soil_moisture_path, "SOIM1")

# Creating aoil moisture vector grid
soil_moisture_dataarray.create_vector_grid()

# Assigning soil moisture values to each road segment
gdf.assign_soil_moisture(soil_moisture_dataarray.grid)

# 

