#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 30 17:17:14 2025

@author: brunojalowski
"""
import pandas as pd
import numpy as np


def Estimativa_SO2(EF_Folder: str, TiposdeCombustivel, MATRIZ_LEVES,
                   MATRIZ_comLEVES, MATRIZ_MOTOS, MATRIZ_PESADOS):
    
    print('***ESTIMANDO AS EMISSÕES DE SO2 PARA OS VEÍCULOS LEVES - BR***')
    filename = EF_Folder + '\EF_SO2_Pollutant\EF_LightDuty_SO2.xlsx'
    
    df = pd.read_excel(filename, engine='openpyxl')  
    df = df.iloc[1:]
    
    # Exemplo: TiposdeCombustivel = [['GASOLINA', 1], ['ALCOOL', 2], ['FLEX GASOLINA', 3], ['FLEX ETANOL', 4]]
    TiposdeCombustivel = pd.DataFrame(TiposdeCombustivel, columns=['Combustivel', 'Codigo'])
    num = df.copy()
    
    # Mapeamentos
    codigoGASOLINA = TiposdeCombustivel.loc[TiposdeCombustivel['Combustivel'] == 'GASOLINA', 'Codigo'].values[0]
    num.loc[df.iloc[:, 1] == 'Gasolina', df.columns[1]] = codigoGASOLINA
    
    codigoETANOL = TiposdeCombustivel.loc[TiposdeCombustivel['Combustivel'] == 'ALCOOL', 'Codigo'].values[0]
    num.loc[df.iloc[:, 1] == 'Etanol', df.columns[1]] = codigoETANOL
    
    codigoFLEXGASOLINA = TiposdeCombustivel.loc[TiposdeCombustivel['Combustivel'] == 'FLEX GASOLINA', 'Codigo'].values[0]
    num.loc[df.iloc[:, 1] == 'Flex Gasolina', df.columns[1]] = codigoFLEXGASOLINA
    
    codigoFLEXETANOL = TiposdeCombustivel.loc[TiposdeCombustivel['Combustivel'] == 'FLEX ETANOL', 'Codigo'].values[0]
    num.loc[df.iloc[:, 1] == 'Flex Etanol', df.columns[1]] = codigoFLEXETANOL
    
    ano_inicio = MATRIZ_LEVES.iloc[:, 3].min()
    ano_fim = num.iloc[:, 0].min() - 1
    
    # Gera os anos faltantes
    anos_faltantes = np.arange(ano_inicio, ano_fim + 1)
    
    # Duplicando os anos (como em sort([anos; anos]) no MATLAB)
    anos_faltantes = np.sort(np.concatenate([anos_faltantes, anos_faltantes]))
    
    # Repetindo os dados de num (linhas 0 e 1, colunas 1 até o fim)
    dados_repetidos = np.tile(num.iloc[0:2, 1:].to_numpy(), (len(anos_faltantes), 1))
    
    # Concatenando os anos com os dados repetidos
    anosfaltantes_df = pd.DataFrame(
        np.concatenate([anos_faltantes.reshape(-1, 1), dados_repetidos], axis=1),
        columns=num.columns
    )
    
    # Juntando com o DataFrame original
    num = pd.concat([anosfaltantes_df, num], ignore_index=True)

    MATRIZ_LEVES['Teor_SO2'] = np.nan
    
    for ii in range(len(num)):
        print(f'***VEICULOS LEVES__SO2 - BR*** {ii+1}/{len(num)}')
    
        # Seleciona o ano e tipo de combustível da linha atual de 'num'
        ano_modelo = num.iloc[ii, 0]
        tipo_combustivel = num.iloc[ii, 1]
        teor_enxofre = num.iloc[ii, 3]  # coluna 4 em MATLAB → index 3 em Python
    
        # Filtra as linhas de MATRIZ_LEVES onde coluna 4 e 5 (index 3 e 4) casam com os valores
        condicao = (MATRIZ_LEVES.iloc[:, 3] == ano_modelo) & (MATRIZ_LEVES.iloc[:, 4] == tipo_combustivel)
    
        # Atribui o valor do teor de enxofre na última coluna
        MATRIZ_LEVES.loc[condicao, 'Teor_SO2'] = teor_enxofre

    cond_gasolina = (MATRIZ_LEVES.iloc[:, 0] == 2013) & \
                    (MATRIZ_LEVES.iloc[:, 4] == 5) & \
                    (MATRIZ_LEVES.iloc[:, -1] == 0.05)
    MATRIZ_LEVES.loc[cond_gasolina, MATRIZ_LEVES.columns[-1]] = 0.8
    
    # Atualiza fator de emissão para veículos leves FLEX gasolina em 2013
    cond_flex = (MATRIZ_LEVES.iloc[:, 0] == 2013) & \
                (MATRIZ_LEVES.iloc[:, 4] == 4) & \
                (MATRIZ_LEVES.iloc[:, -1] == 0.05)
    MATRIZ_LEVES.loc[cond_flex, MATRIZ_LEVES.columns[-1]] = 0.8
    
    # Cálculo da emissão de SO2
    # MATRIZ_LEVES colunas 15 a 18 correspondem a colunas 16-19 do MATLAB
    EmissoesSO2 = MATRIZ_LEVES.iloc[:, 0:6].copy()
    emissoes_valor = MATRIZ_LEVES.iloc[:, [15, 16, 17, 18]].prod(axis=1)
    EmissoesSO2['SO2'] = emissoes_valor.fillna(0)
    
    # Consolidação por cidade (ano, UF, município)
    EmissCityLevesSO2 = EmissoesSO2.groupby([EmissoesSO2.columns[0], 
                                             EmissoesSO2.columns[1], 
                                             EmissoesSO2.columns[2]])['SO2'].sum().reset_index()
    
    # Consolidação por UF (ano, UF)
    EmissUFLevesSO2 = EmissoesSO2.groupby([EmissoesSO2.columns[0], 
                                           EmissoesSO2.columns[1]])['SO2'].sum().reset_index()
    
    # Estimativa para veículos comerciais leves
    print('***ESTIMANDO AS EMISSOES DE SO2 PARA OS VEICULOS COMERCIAIS LEVES - BR***')
    
    # Leitura da planilha Excel com fatores de emissão
    EF_folder = 'CAMINHO/DA/PASTA'  # substitua com o caminho correto
    filename = f'{EF_folder}/EF_SO2_Pollutant/EF_LightCommercial_SO2.xlsx'
    EF_LightCommercial = pd.read_excel(filename, skiprows=1)

    return EmissCityLevesSO2, EmissCityComLevesSO2, EmissCityMotosSO2, EmissCityPesadosSO2