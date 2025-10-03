#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr 28 13:25:21 2025

@author: brunojalowski
"""
import pandas as pd

def vehicular_weight(fleet_path: str,
                     light_duty_weight = 1.1485,
                     heavy_duty_weight = 16.0,
                     motorcycle_weight = 0.128):
    """
    This function calculates de average vehicular weight for each city based 
    on fleet composition and median weight for each vehicle category

    Parameters
    ----------
    fleet_path : str
        DESCRIPTION.
    lightduty_weight : int or float, optional
        DESCRIPTION. The default is 1.1485.
    heavyduty_weight : int or float, optional
        DESCRIPTION. The default is 16.0.
    motorcycle_weight : int or float, optional
        DESCRIPTION. The default is 0.128.

    Returns
    -------
    df : TYPE
        DESCRIPTION.

    """
    # Reading file containing vehicle fleet
    df = pd.read_excel(fleet_path, skiprows=3)

    # Reclassifying vehicles
    df['light_duty'] = df.loc[:, ['AUTOMOVEL',
                                  'BONDE',
                                  'CAMINHONETE',
                                  'CAMIONETA',
                                  'UTILITARIO',
                                  'OUTROS']].sum(1)

    df['motorcycles'] = df.loc[:, ['CICLOMOTOR',
                                    'MOTOCICLETA',
                                    'MOTONETA',
                                    'QUADRICICLO',
                                    'SIDE-CAR',
                                    'TRICICLO']].sum(1)

    df['heavy_duty'] = df.loc[:, ['CAMINHAO',
                                  'CAMINHAO TRATOR',
                                  'CHASSI PLATAF',
                                  'MICRO-ONIBUS',
                                  'ONIBUS',
                                  'REBOQUE',
                                  'SEMI-REBOQUE',
                                  'TRATOR ESTEI',
                                  'TRATOR RODAS']].sum(1)

    # Calculating mean_weight for each city
    df['average_weight'] = ((df.loc[:, 'light_duty'] * light_duty_weight +
                             df.loc[:, 'motorcycles'] * motorcycle_weight +
                             df.loc[:, 'heavy_duty'] * heavy_duty_weight) /
                            df.loc[:, 'TOTAL'])
    
    # Removing external spaces
    df['MUNICIPIO'] = df['MUNICIPIO'].str.strip()
    # Removing internal spaces
    df['MUNICIPIO'] = df['MUNICIPIO'].str.replace(' ', '', regex=False)
    # Removing non-ASCII characters
    df['MUNICIPIO'] = df['MUNICIPIO'].str.replace(r"[\'\-]", "", regex=True)
    


    return df