#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar 21 11:17:19 2025

@author: brunojalowski

Dados de umidade do solo do CMIP da WRF. 
A variável de interesse é SOIM1 = volumetric soil moisture in near-surface soil (m3.m-3).

"""
#%% Importando pacotes
import xarray as xr
import matplotlib.pyplot as plt
import netcdf4_conversions_v2 as conv
import numpy as np
from road_preprocess import gdf
import geopandas as gpd
from shapely.geometry import box, LineString

#%%Abrindo o dataset da WRF
xds = xr.open_mfdataset('/home/brunojalowski/Documentos/RD_Vehic_Resusp/dados_entrada/Soil Moisture/METCRO2D_BR_20km_2023-02-01.nc')
print(xds.dims)

#%%Definição das coordenadas LAT e LON do dataset 
xds = conv.brain_to_latlng(xds) 

#%%Localizar a variável de soil moisture
soil_moisture = xds['SOIM1'] #SOIM1 = volumetric soil moisture in near-surface soil (m3.m-3)

#%%Passando o geodataframe para o mesmo CRS de soil_moisture
gdf = gdf.to_crs(soil_moisture.rio.crs)

#%%Plotando os dois para ver se encaixam

fig, ax = plt.subplots()
xr.plot.pcolormesh(darray=soil_moisture[0,0,:,:],ax=ax)
gdf.plot(ax=ax, color="r")
ax.set_xlim(gdf.bounds.minx.min()-0.01,gdf.bounds.maxx.max()+0.01)
ax.set_ylim(gdf.bounds.miny.min()-0.01,gdf.bounds.maxy.max()+0.01)
plt.show()


#%% Vectorizing soil_moisture dataset

# Pixels' centroids from soil_moisture
lons = soil_moisture['lon'].values
lats = soil_moisture['lat'].values

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
soil_grid = gpd.GeoDataFrame(geometry=grid_cells, crs="EPSG:4326")
soil_grid['i_index'] = i_indexes
soil_grid['j_index'] = j_indexes


# Get the soil moisture values as a 2D array
values = soil_moisture.isel(TSTEP=0,LAY=0).values

# Map the values to the grid cells
soil_grid['value'] = [values[i, j] 
                      for i, j 
                      in zip(soil_grid['i_index'], soil_grid['j_index'])]

# Drop the indices
soil_grid = soil_grid.drop(columns=['i_index', 'j_index'])

#%%Plotando o soil_moisture vetorizado

fig, ax = plt.subplots(figsize=(10, 8))

# Plot soil_moisture data (first timestep and level)
#xr.plot.pcolormesh(darray=soil_moisture[0,0,:,:], ax=ax)

# Plot soil_grid polygons colored by 'value' column
soil_grid.plot(
    ax=ax, 
    column='value',    
    edgecolor='black',       
    linewidth=0.5,         
    alpha=0.7,             
    cmap='viridis',       
    legend=True,            
    legend_kwds={
        'label': "Soil Moisture Value",
        'shrink': 0.7               
    }
)
ax.set_xlim(gdf.bounds.minx.min()-1,gdf.bounds.maxx.max()+1)
ax.set_ylim(gdf.bounds.miny.min()-1,gdf.bounds.maxy.max()+1)
plt.title("Soil Moisture with Grid Cell Values")
plt.show()

# %% Assigning soil_moisture values proportional to road fraction inside each 
# pixel

def assigning_soil_moisture(line: LineString,
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

# %% Assigning soil moisture to roads

values = []
for ii in range(gdf.shape[0]):
        line = gdf.geometry.iloc[ii]
        value = assigning_soil_moisture(line, soil_grid)
        if value > 0 :
            values.append(value)
        else:
            values.append(None)

gdf['soil_moisture'] = values






