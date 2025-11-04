#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Nov  3 17:23:41 2025

@author: brunojalowski
"""
from pathlib import Path
import xarray as xr
import glob
from datetime import datetime


mcip_path = Path('../inputs/soil_moisture/').resolve()
outputs_path = Path('../outputs').resolve()
process04_outputs_path = outputs_path / 'process04'

YEAR = 2023

# Listing all mcip files
mcip_files = glob.glob(str(mcip_path / '*.nc'))

# Filtering other years
mcip_files = [f for f in mcip_files if str(YEAR) in f]
mcip_files = sorted(mcip_files)


"""
Variáveis com suas descrições:
TFLAG: Timestep-valid flags:  (1) YYYYDDD or (2) HHMMSS                                
PRSFC: surface pressure                                                                
USTAR: cell averaged friction velocity                                                 
WSTAR: convective velocity scale                                                       
PBL: PBL height                                                                      
ZRUF: surface roughness length                                                        
MOLI: inverse of Monin-Obukhov length                                                 
HFX: sensible heat flux                                                              
LH: latent heat flux                                                                
RADYNI: inverse of aerodynamic resistance                                               
RSTOMI: inverse of stomatic resistance                                                  
TEMPG: skin temperature at ground                                                      
TEMP2: temperature at 2 m                                                              
Q2: mixing ratio at 2 m                                                             
WSPD10: wind speed at 10 m                                                              
WDIR10: wind direction at 10 m                                                          
GLW: longwave radiation at ground                                                    
GSW: solar radiation absorbed at ground                                              
RGRND: solar radiation reaching ground                                                 
RN: nonconvective precipitation in interval                                         
RC: convective precipitation in interval                                            
CFRAC: total cloud fraction                                                            
CLDT: cloud top layer height                                                          
CLDB: cloud bottom layer height                                                       
WBAR: average liquid water content of cloud                                           
SNOCOV: snow cover                                                                      
VEG: vegetation coverage                                                             
LAI: leaf-area index                                                                 
SEAICE: sea ice                                                                         
SNOWH: snow height                                                                     
WR: canopy moisture content                                                         
SOIM1: volumetric soil moisture in top cm                                              
SOIM2: volumetric soil moisture in top m                                               
SOIT1: soil temperature in top cm                                                      
SOIT2: soil temperature in top m                                                       
SLTYP: soil texture type by USDA category                                              
"""

ds = xr.open_mfdataset(mcip_files[0])


# Listing years
years = [int(str(path).split('/')[-1]) 
         for path 
         in list(Path(process04_outputs_path).glob('*/'))]

for year in years:
    # Selecting all files of the year
    year_files = [f for f in mcip_files if str(year) in f]
    
    for file in year_files:
        evap_ds = xr.open_dataset(file)[['RN', 'PRSFC', 'SOIM1',
                                           'TEMP2', 'Q2']]
    
    