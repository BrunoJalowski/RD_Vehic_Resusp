#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr  8 17:18:46 2025

@author: brunojalowski
"""
# Importing main dataframe
from emissions import gdf_filtered

#%% Importing dependencies
import matplotlib.pyplot as plt
import netcdf4_conversions_v2 as conv
import numpy as np
from shapely.geometry import box
import geopandas as gpd
import xarray as xr
from mpl_toolkits.axes_grid1 import make_axes_locatable
import matplotlib.cm as cm
import matplotlib.colors as colors

#%% Opening CMIP's dataset
xds = xr.open_mfdataset('/home/brunojalowski/Documentos/RD_Vehic_Resusp/dados_entrada/Soil Moisture/METCRO2D_BR_20km_2023-02-01.nc')

#Defining dataset's LAT and LON coordinates 
xds = conv.brain_to_latlng(xds) 

#Localizing variable soil moisture
soil_moisture = xds['SOIM1'] #SOIM1 = volumetric soil moisture in near-surface soil (m3.m-3)



#%% Definition of the grid aligned with pixels and resolution of soil_moisture dataset

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
for i in range(len(lat_edges) - 1):
    for j in range(len(lon_edges) - 1):
        cell = box(
            lon_edges[j],
            lat_edges[i],
            lon_edges[j + 1],
            lat_edges[i + 1]
        )
        grid_cells.append(cell)

# Turns it into a GeoDataFrame
grid = gpd.GeoDataFrame(geometry=grid_cells, crs="EPSG:4326")

#%%
# Plotting grid over dataset to see if it fits
fig, ax = plt.subplots(figsize=(15, 10))
xr.plot.pcolormesh(darray=soil_moisture[0,0,:,:],ax=ax)
grid.boundary.plot(ax=ax, color='gray', linestyle='--', linewidth=0.5)


#%%

def emissions_by_pixel(cell, pollutant, emissions):
    """ This function calculates the total amount emitted within the boundaries of the selected cell.

    Args:
        cell (grid.geometry[i]): grid cell in which aggregate the emissions 

        pollutant (str): column name with emission values

        emissions (GeoDataFrame): geodataframe with emission values 

    Returns:
        float: sum of all emissions from all lines that intersect the cell, proportional to the
        percentage of each line that is inside the cell.
    """
    
    # Selects only lines that intersect with the cell
    intersected_lines = emissions[emissions.intersects(cell)].copy()
    if intersected_lines.empty:
        return np.nan
    
    # Comprimento total das linhas
    intersected_lines["total_length"] = intersected_lines.geometry.length
    
    # Comprimento da parte da linha que está dentro da célula
    intersected_lines["intersected_length"] = intersected_lines.geometry.intersection(cell).length
    
    # Peso proporcional ao comprimento dentro da célula
    intersected_lines["weight_factor"] = intersected_lines["intersected_length"] / intersected_lines["total_length"]
    
    # Emissão ponderada
    return (intersected_lines[pollutant] * intersected_lines["weight_factor"]).sum()

#%%
valores = []
for i in grid.index:
        cell = grid.geometry[i]
        valor = emissions_by_pixel(cell, '25_emission', gdf_filtered)
        if valor > 0 :
            valores.append(np.log10(valor))
        else:
            valores.append(None)

grid['25_emission'] = valores

#%% PLOT DE FLUXOS
fig, ax = plt.subplots()

# Define os limites do raster
minx, miny, maxx, maxy = gdf_filtered.total_bounds
extent = (minx, maxx, miny, maxy)

# Limites de valor de emissao
vmin = grid['25_emission'].min()
vmax = grid['25_emission'].max()
norm = colors.Normalize(vmin=vmin, vmax=vmax)

#Emissao
grid.plot(
    ax=ax,
    column='25_emission',
    cmap='hot_r',  
    linewidth=0.8,
    alpha=0.8)

#Vias
gdf_filtered.plot(ax=ax, color="r")

# Colorbar
sm = cm.ScalarMappable(norm=norm, cmap='hot_r')
sm.set_array([])  
cbar = fig.colorbar(sm, ax=ax, fraction=0.03, pad=0.04)
cbar.set_label('Emissão (g/s)')

ax.set_xlim(minx, maxx)
ax.set_ylim(miny, maxy)
ax.set_title('Emissão PM2.5')
ax.set_xlabel('Longitude')
ax.set_ylabel('Latitude')
ax.set_facecolor('grey')
plt.tight_layout()


#%%
fig, ax = plt.subplots(1,3, figsize=(12,8))
minx, miny, maxx, maxy = gdf_filtered.total_bounds


## EMISSÃO
# Limites de valor de emissao
vmin = grid['25_emission'].min()
vmax = grid['25_emission'].max()
norm = colors.Normalize(vmin=vmin, vmax=vmax)

grid.plot(
    ax=ax[0],
    column='25_emission',
    cmap='hot_r',  
    linewidth=0.8,
    alpha=0.8)

ax[0].set_xlim(minx, maxx)
ax[0].set_ylim(miny, maxy)
ax[0].set_title('Emissões de PM2.5')
ax[0].set_xlabel('Longitude')
ax[0].set_ylabel('Latitude')
ax[0].set_facecolor('grey')
ax[0].tick_params(axis='both', labelsize=8)





## FLUXO
vmin_flow = gdf_filtered[gdf_filtered['flow']>0]['flow'].min()
vmax_flow = gdf_filtered['flow'].max()
norm_flow = colors.LogNorm(vmin=vmin_flow, vmax=vmax_flow)

# Colormap e colorbar
sm = cm.ScalarMappable(norm=norm_flow, cmap='Blues')  # ou qualquer cmap que quiser
sm.set_array([])
cbar = fig.colorbar(sm, ax=ax[1], fraction=0.03, pad=0.04)
cbar.set_label('Fluxo')

grid.boundary.plot(ax=ax[1],color='b', linewidth=0.2)
gdf_filtered.plot(ax=ax[1],column='flow',norm=norm_flow, cmap='Blues')

ax[1].set_xlim(minx, maxx)
ax[1].set_ylim(miny, maxy)
ax[1].set_title('Fluxo')
ax[1].set_xlabel('Longitude')
ax[1].set_ylabel('Latitude')
ax[1].set_facecolor('grey')
ax[1].tick_params(axis='both', labelsize=8)



## SOBREPOSIÇÃO
grid.plot(
    ax=ax[2],
    column='25_emission',
    cmap='hot_r',
    linewidth=0.8,
    alpha=0.8
)

# Vias com coloração por fluxo
gdf_filtered.plot(
    ax=ax[2],
    column='flow',
    cmap='Blues',
    norm=norm_flow,  
    linewidth=1.2
)

divider = make_axes_locatable(ax[2])

# Colorbar para emissão (à direita)
cax_emission = divider.append_axes("right", size="5%", pad=0.05)
sm_emission = cm.ScalarMappable(norm=norm, cmap='hot_r')
sm_emission.set_array([])
cbar_emission = plt.colorbar(sm_emission, cax=cax_emission)
cbar_emission.set_label('Emissão 2.5')

# Colorbar para fluxo (embaixo)
cax_flow = divider.append_axes("bottom", size="5%", pad=0.5)
sm_flow = cm.ScalarMappable(norm=norm_flow, cmap='Blues')
sm_flow.set_array([])
cbar_flow = plt.colorbar(sm_flow, cax=cax_flow, orientation="horizontal")
cbar_flow.set_label('Fluxo')

# Ajustes
ax[2].set_xlim(minx, maxx)
ax[2].set_ylim(miny, maxy)
ax[2].set_title('Sobreposição')
ax[2].set_xlabel('Longitude')
ax[2].set_ylabel('Latitude')
ax[2].set_facecolor('grey')
ax[2].tick_params(axis='both', labelsize=8)
plt.tight_layout()

#%% SOBREPOSIÇÃO FLUXO E EMISSOES
fig, ax = plt.subplots(figsize=(8,8))
minx, miny, maxx, maxy = gdf_filtered.total_bounds

vmin_flow = gdf_filtered[gdf_filtered['flow']>0]['flow'].min()
vmax_flow = gdf_filtered['flow'].max()
vmin_25 = gdf_filtered[gdf_filtered['flow']>0]['25_emission'].min()
vmax_25 = gdf_filtered['25_emission'].max()

norm_flow = colors.LogNorm(vmin=vmin_flow, vmax=vmax_flow)
norm_25 = colors.LogNorm(vmin=vmin_25, vmax=vmax_25)

grid.plot(
    ax=ax,
    column='25_emission',
    cmap='hot_r',
    linewidth=0.8,
    alpha=0.8
)

# Vias com coloração por fluxo
gdf_filtered.plot(
    ax=ax,
    column='flow',
    cmap='RdGy',
    norm=norm_flow,  
    linewidth=1.2
)

divider = make_axes_locatable(ax)

# Colorbar para emissão (à direita)
cax_emission = divider.append_axes("right", size="5%", pad=0.05)
sm_emission = cm.ScalarMappable(norm=norm_25, cmap='hot_r')
sm_emission.set_array([])
cbar_emission = plt.colorbar(sm_emission, cax=cax_emission)
cbar_emission.set_label('Emissão 2.5')

# Colorbar para fluxo (embaixo)
cax_flow = divider.append_axes("bottom", size="5%", pad=0.5)
sm_flow = cm.ScalarMappable(norm=norm_flow, cmap='RdGy')
sm_flow.set_array([])
cbar_flow = plt.colorbar(sm_flow, cax=cax_flow, orientation="horizontal")
cbar_flow.set_label('Fluxo')

# Ajustes
ax.set_xlim(minx, maxx)
ax.set_ylim(miny, maxy)
ax.set_title('Sobreposição Fluxo e Emissões de PM2.5')
ax.set_xlabel('Longitude')
ax.set_ylabel('Latitude')
ax.set_facecolor('grey')
ax.tick_params(axis='both', labelsize=8)
plt.tight_layout()