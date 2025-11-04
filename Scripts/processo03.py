#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr 28 13:25:21 2025

@author: brunojalowski
"""
import pandas as pd
import glob
import numpy as np
from pathlib import Path

#%% Paths
inputs_path = Path('../inputs').resolve()
outputs_path = Path('../outputs/vehicular_weight').resolve()
fleet_path = inputs_path / 'Vehicular_Weight'
frota_categoria_processada_path = inputs_path / 'frota_categoria_processada.csv'


#%% AVERAGE WEIGHT FUNCTION

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
        DESdfCRIPTION.
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
    months_order = {
        "janeiro": 1, "fevereiro": 2, "marco": 3, "abril": 4,
        "maio": 5, "junho": 6, "julho": 7, "agosto": 8,
        "setembro": 9, "outubro": 10, "novembro": 11, "dezembro": 12
    }
    
    # Function for extracting month number from filename
    def extract_month_nmbr(filename):
        for month in months_order:
            if month in filename.lower():
                return months_order[month]
        return 0
    
    
    # Reading file containing vehicle fleet
    files = glob.glob(str(Path(fleet_path) / '*.xls'))
    
    # Sorting based on month
    files = sorted(files, key=extract_month_nmbr)
    
    # Reading file and applying weight function
    for idx,file in enumerate(files):
        
        # Reading file
        df = pd.read_excel(file)
        
        for idx_2, value in enumerate(df.iloc[:, 0]):
            if value == 'UF':
                break
            
        header = df.iloc[idx_2].to_numpy()
        
        df = df.iloc[idx_2 + 1:, :]
        df.columns = header
        df = df.reset_index(drop=True)
            
        #FIXME VERIFICACAO
        if 'MUNICIPIO' in df['MUNICIPIO'].astype(str).str.upper().values:
            print(f"\n⚠️  Atenção: O arquivo '{file}' contém uma linha com 'MUNICIPIO' nos dados!")
            
            df = df.iloc[1:, :]
            df.columns = header
            df = df.reset_index(drop=True)
        
        # Reclassifying vehicles into wider categories
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
        
        cols_to_convert = ['light_duty', 'motorcycles', 'heavy_duty', 'TOTAL']
        
        for col in cols_to_convert:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
        # Calculating mean_weight for each city
        df['average_weight'] = (
            (df.loc[:, 'light_duty'] * light_duty_weight +
             df.loc[:, 'motorcycles'] * motorcycle_weight +
             df.loc[:, 'heavy_duty'] * heavy_duty_weight) /
             df.loc[:, 'TOTAL'])
        
        # Removing external spaces
        df['MUNICIPIO'] = df['MUNICIPIO'].str.strip()
        # Removing internal spaces
        df['MUNICIPIO'] = df['MUNICIPIO'].str.replace(' ',
                                                      '',
                                                      regex=False)
        # Removing non-ASCII characters
        df['MUNICIPIO'] = df['MUNICIPIO'].str.replace(r"[\'\-]",
                                                      "",
                                                      regex=True)
        
        
        #%% LINKING CITY NAMES TO IBGE CODES
        # Applying IBGE code
        """This file is an intermediary dataframe named frota_categoria_processada, 
        after the function adicionando_codigo_ibge_mun_especiais_sem_espaco, from
        BRAVES's main code."""
        
        frota_categoria_processada = pd.read_csv(frota_categoria_processada_path)
        
        # Correcting Inconsistencies in city names
        corrections = {
            'ARMACAODEBUZIOS': 'ARMACAODOSBUZIOS',
            'BARAODMONTEALTO': 'BARAOD0MONTEALTO',
            'EMBU': 'EMBUDASARTES',
            'NOVADOMAMORE': 'NOVAMAMORE',
            'POXOREO': 'POXOREU',
            'BRAZOPOLIS': 'BRASOPOLIS',
            'GOUVEIA': 'GOUVEA'
            }
        
        frota_categoria_processada['MUNICIPIO'] = (
            frota_categoria_processada['MUNICIPIO']
            .replace(corrections)
            )
        
        df['MUNICIPIO'] = df['MUNICIPIO'].replace(corrections)
        
        
        # Dropping cities without name or code
        df = df.loc[df['MUNICIPIO'] != 'MUNICIPIONAOINFORMADO']
        df = df.dropna(subset='MUNICIPIO', axis=0)
        
        # Merging vehicle weight and city names
        df = pd.merge(df,
                      frota_categoria_processada[['UF',
                                                  'MUNICIPIO',
                                                  'CODIGO IBGE']],
                      on=['UF','MUNICIPIO'],
                      how='left')
        
        #FIXME VERIFICAÇÂO
        missing_codes = df[df['CODIGO IBGE'].isna()]
        
        if not missing_codes.empty:
            print(f"Atenção: {len(missing_codes)} municípios sem código IBGE encontrado:")
            print(missing_codes['MUNICIPIO'].unique())
        
        
        # Adding IBGE code for "IBITIUVA"
        df.loc[df['MUNICIPIO'] == 'IBITIUVA','CODIGO IBGE'] = 3521508
        
        # Take it out of scientific notation
        df['CODIGO IBGE'] = (
            df['CODIGO IBGE']
            .astype(int)
            .astype(str)
            .astype(int)
            )
        
        
        if idx == 0:
            weight_df = pd.DataFrame({
                'UF': df['UF'],
                'MUNICIPIO': df['MUNICIPIO'],
                'CODIGO IBGE': df['CODIGO IBGE'],
                f'average_weight_{idx+1}': df['average_weight'].astype(np.float32)
                })
            
        else:
            weight_df = weight_df.merge(
                df[['UF','MUNICIPIO','CODIGO IBGE', 'average_weight']]
                .rename(
                    columns={'average_weight': f'average_weight_{idx+1}'}
                    ),
                on=['UF','MUNICIPIO','CODIGO IBGE'],
                how='left'
                )
            
    


    return weight_df


#%% CALCULATING AVERAGE WEIGHT AND SAVING

fleet_path_list = [str(path)
                   for path 
                   in list(Path(fleet_path).glob('frota_munic_modelo_*'))]

fleet_path_list = sorted(fleet_path_list)

# Applying weight function
for fleet_path in fleet_path_list:
    year = int(str(fleet_path).split('_')[-1])
    
    # Applying function
    weight_df = vehicular_weight(fleet_path=fleet_path)
    
    # Saving to file
    weight_df.to_parquet(outputs_path / f'peso_medio_{year}.parquet')


