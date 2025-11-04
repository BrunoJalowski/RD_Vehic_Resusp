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
import netcdf4_conversions_v2 as conv
import numpy as np

#%%
inputs_path = Path('../inputs').resolve()

soil_moisture_path = (inputs_path /
                      'Soil Moisture/METCRO2D_BR_20km_2023-02-01.nc')

#%%

#Abrindo o dataset da WRF
xds = xr.open_mfdataset(soil_moisture_path)

#Definição das coordenadas LAT e LON do dataset 
xds = conv.brain_to_latlng(xds) 

#%%Localizar a variável de soil moisture
# =============================================================================
# soil_moisture = xds['SOIM1'][:,0,:,:] #SOIM1 = volumetric soil moisture in near-surface soil (m3.m-3)
# =============================================================================

#%%






























#%% Associating cell_id and coordinates

""" 
Grade original do MCIP usada é de 408 x 381, totalizando 155448 ids
OBS: cell_id é contado a partir do 0

lat_idx = int((cell_id + 1) /  381) 

long_idx = (cell_id +1) % 381 

"""

def get_pixel_coords_from_cell_id(cell_id_col:np.ndarray,
                                  n_of_cols: int):
    """
    

    Parameters
    ----------
    cell_id_col : np.ndarray
        DESCRIPTION.

    Returns
    -------
    None.

    """
    unique_ids = np.unique(cell_id_col)
    
    
    """+1 is correcting the fact that the indexes start at 0 and the -1 is
    correcting the difference between the 2 versions of mcip grid (remove -1
    when using the correct grid)"""
    
    lat_idx = ((unique_ids + 1) / n_of_cols).astype(int) -1 
    lon_idx = (unique_ids + 1) % n_of_cols -1 -1
    
    coords = [[y,x] for y,x in zip(lat_idx, lon_idx)]
    
    return coords

pixels_coords = get_pixel_coords_from_cell_id(gdf.cell_id, 259)



#%%Plotando os dois para ver se encaixam
# =============================================================================
# 
# fig, ax = plt.subplots()
# xr.plot.pcolormesh(darray=soil_moisture[0,0,:,:],ax=ax)
# gdf.plot(ax=ax, color="r")
# ax.set_xlim(gdf.bounds.minx.min()-0.01,gdf.bounds.maxx.max()+0.01)
# ax.set_ylim(gdf.bounds.miny.min()-0.01,gdf.bounds.maxy.max()+0.01)
# plt.show()
# 
# 
# =============================================================================





