#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Oct 31 12:14:20 2025

@author: brunojalowski
"""

# %% IMPORTING MODULES ========================================================
import xarray as xr
from pathlib import Path
import pandas as pd
import glob
import numpy as np

import ef_functions as ef
from is_leap_year import is_leap_year
import netcdf4_conversions_v2 as conv

from PAVED_p_adapted import creditsf_vectorized, nmf_vectorized
from UNPAVED_p_adapted import nmf_precipitation
from REL_HUM_rh import relhum
from AP42_2_m import surf_moist
from MOIS_h import soilmoist_correc
from UNPAVED_p_h import nat_mit_fact
from TRANS_FRAC_f import trans_frac


# %% PATHS ===================================================================
inputs_path = Path('../inputs').resolve()

outputs_path = Path('../outputs').resolve()

process04_outputs_path = outputs_path / 'process04'

process05_outputs_path = outputs_path / 'process05'

mcip_path = inputs_path / 'Soil Moisture'

# Creating folder for the year if non existant
if not process05_outputs_path.exists():
    process05_outputs_path.mkdir(parents=True, exist_ok=True)

#%%

# Listing all mcip files
mcip_files = glob.glob(str(mcip_path / '*.nc'))

# Listing years
years = [int(str(path).split('/')[-1]) 
         for path 
         in list(Path(process04_outputs_path).glob('*/'))]

# Sorting years in chronologicl order
years = sorted(years, reverse=True) #FIXME RETIRAR O REVERSE

# Iterating over all years available in chronological order
for year in years:
    year_input_folder = Path(process04_outputs_path / f'{year}')
    year_output_folder = process05_outputs_path / f'{year}'
    
    # Creating folder for the year if non existant
    if not year_output_folder.exists():
        year_output_folder.mkdir(parents=True, exist_ok=True)
        
    # Listing all months available
    months = [int(str(path).split('/')[-1]) 
              for path 
              in list(Path(year_input_folder).glob('*/'))
              ]
    
    # Sorting them in cronological order
    months = sorted(months)
    
    # Dict with number of days by month
    days_by_month = {
        1: 31, 2: 28, 3: 31, 4: 30,
        5: 31, 6: 30, 7: 31, 8: 31, 
        9: 30, 10: 31, 11: 30, 12: 31
        }
    
    # Changes number of days for february if year is a leap year
    if is_leap_year(year):
        days_by_month[2] = 29
    

    # Iterating over month folders
    for month in months:
        month_input_folder = year_input_folder / f'{month}'
        month_output_folder = year_output_folder / f'{month}'
        

        # Creating folder for the year if non existant
        if not month_output_folder.exists():
            month_output_folder.mkdir(parents=True, exist_ok=True)
        
        
        # Iterates over all days available for that month is order
        for day in range(1, days_by_month[month] + 1):
        
            #FIXME  
# =============================================================================
#             # Reading industrial and paved emissions file #FIXME
#             ind_n_paved_emission = xr.open_mfdataset(
#                 month_input_folder / 
#                 'industrialAndPavedEmission'
#                 f'_{year}-{month}-{day}.nc'
#                 )
#             
#             # Reading open access partial factor file
#             open_access_partial = xr.open_mfdataset(
#                 month_input_folder / 
#                 f'publicPartial_{year}-{month}-{day}.nc'
#                 )
# =============================================================================
            
            # Formatting date string (adding or not '0' for numbers < 10)
            # MCIP files date format is YYYY-MM-DD
            if month < 10:
                if day < 10:
                    date_format = f'{year}-0{month}-0{day}'
                else:
                    date_format = f'{year}-0{month}-{day}'
            else:
                if day < 10:
                    date_format = f'{year}-{month}-0{day}'
                else:
                    date_format = f'{year}-{month}-{day}'
            
            # Select mcip file for the year, month and day
            for path in mcip_files:
                if date_format in path:
                    mcip_file = path
            
            # Reading mcip file for the year, month and day
            mcip = xr.open_dataset(mcip_file)[['RN', 'PRSFC', 'SOIM1',
                                               'TEMP2', 'Q2']]

            """--------------- Important variables -------------------
            PRSFC: surface pressure 
            SOIM1: volumetric soil moisture in top cm 
            TEMP2: temperature at 2 m                                                              
            Q2: mixing ratio at 2 m
            RN: nonconvective precipitation in interval
            
            """
            
            # Defining Lat and Lon coords
            mcip = conv.brain_to_latlng(mcip) 
            
            # Creating rain dataset
            rain_array = mcip['RN'].squeeze().values  # shape = (25, 247, 257)
            
            ## PAVED ROADS MITIGATION ======================================
            # Calculating natural mitigation factor for all hours and pixels
            nat_mit_factor = nmf_vectorized(rain_array)
            
            # Calculating mitigated emissions for paved and industrial roads
            mitigated_ind_n_paved_emission = (
                ind_n_paved_emission * nat_mit_factor
                )
            
            ## UNPAVED ROADS ===============================================
            
            '''Calculating NMF from precipitation (80% reduction if a 
            precipitation event >0.254mm occurs)'''
            nmfp = nmf_precipitation(rain_array)
            
            '''Calculating the ambient relative humidity per hour neccesary 
            in the surface moisture calculation'''
            rel_hum = relhum(mcip.squeeze())
                    
            ''' Calculating surface moisture per hour'''
            # Variables needed to calculate surface moisture fraction
            TDF = 1.0        # Threshold level for dew point to form
            HRNtoRN = 0.0254 # Relationship between threshold value and Relative Humidity units = cm
            ro = 1440.0      # Road surface density units = kg/m**3 (Appendix A - AP42 Densities of Selected Substances)
            T = 0.25         # Road surface thickness
            MAXMp = 20       # Maximum moisture percentage
            MAXM = 0.1786    #1.125    # Maximum moisture units = cm
            MINMp = 0.2      # Minimum moisture percentage
            AHE = 12./8760   # Average Hourly Evaporation (month = 12 / 8760)
            EC = 0.75 * AHE  # Evaporation Constant
            EM =  #FIXME
            VH =  #FIXME
            HOURLY_EVAP = ((EC * EM * VH) / MAXM) # hourly water loss in fraction of maximum water in cm
            Mp_LOWER_BOUND = MINMp / MAXMp        # minimum percent of maximum moisture        
            
            # Calculating surface moisture
            surf_moisture = surf_moist(rain_array, rel_hum)
            
            # 
            
            
                
                
            
            
            
            
            
            
            
            
            
            
            
            
            
            break
        break
    break
