#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May  5 09:27:45 2025

@author: brunojalowski
"""
import numpy as np
from pathlib import Path
import pandas as pd

def SalvaArquivosTXT_BRAVES(path, EmissCityComLevesBR, EmissCityLevesBR,
                            EmissCityMotosBR, EmissCityPesadosBR):
    # Cria diretório de saída usando Path
    output_path = Path(path) / 'OUTPUT'
    output_path.mkdir(parents=True, exist_ok=True)

    # Cabeçalho veículos comerciais leves
    headerCOMLEVES = ('YEAR_DATA, UF_CODE, MUN_CODE, EmisscomLevesCO,'
                      'EmisscomLevesHC,EmisscomLevesNMHCescape,'
                      'EmisscomLevesCH4, EmisscomLevesNOx,'
                      'EmisscomLevesRCHO, EmisscomLevesMP, EmisscomLevesCO2,'
                      'EmisscomLevesN2O, EmisscomLevesSO2,'
                      'EmisscomLevesNMHCabastece, EmisscomLevesCO2eq,'
                      'EmisscomLevesMP10pneu_freio,EmisscomLevesMP10pista,'
                      'EmisscomLevesMP10Ressuspensao, EmisscomLevesNMHCDiurnal,'
                      'EmisscomLevesNMHCHotSoak, EmisscomLevesNMHCRunningL')

    # Salvar todos os dados em um único arquivo
    print('Salvando os Dados de Emissao dos Comerciais Leves por cidade (.txt)')
    all_file = output_path / 'EmissCityComLeves_BRAVES.txt'
    with all_file.open('w', encoding='utf-8') as f:
        f.write(headerCOMLEVES)
        for row in EmissCityComLevesBR:
            f.write(', '.join(f'{value:.5f}' if isinstance(value, float) else f'{int(value)}' for value in row) + '\n')

    # Salvar arquivos para os anos de 2013 a 2018
    anos_desejados = range(2013, 2019)
    anos_coluna = EmissCityComLevesBR[:, 0]

    for ano in anos_desejados:
        print(f'Salvando os Dados de Emissao dos Comerciais Leves {ano} por cidade (.txt)')
        dados_ano = EmissCityComLevesBR[anos_coluna == ano]

        file_ano = output_path / f'EmissCityComLeves_BRAVES_{ano}.txt'
        with file_ano.open('w', encoding='utf-8') as f:
            f.write(headerCOMLEVES)
            for row in dados_ano:
                f.write(', '.join(f'{value:.5f}' if isinstance(value, float) else f'{int(value)}' for value in row) + '\n')
    
    #-------------------------------VEICULOS LEVES-----------------------------
    
    # Cabeçalho veículos leves
    headerLEVES = ('YEAR_DATA, UF_CODE, MUN_CODE, EmissLevesCO,' 
                      'EmissLevesHC, EmissLevesNMHCescape,'
                      'EmissLevesCH4, EmissLevesNOx,'
                      'EmissLevesRCHO, EmisslevesMP, EmissLevesCO2, '
                      'EmissLevesN2O, EmissLevesSO2, '
                      'EmissLevesNMHCabastece, EmissLevesCO2eq, '
                      'EmissLevesMP10pneu_freio, EmissLevesMP10pista, '
                      'EmissLevesMP10Ressuspensao, EmissLevesNMHCDiurnal, '
                      'EmissLevesNMHCHotSoak, EmissLevesNMHCRunningL')

    # Salvar todos os dados juntos
    print('Salvando os Dados de Emissao dos Leves por cidade (.txt)')
    all_file = output_path / 'EmissCityLeves_BRAVES.txt'
    with all_file.open('w', encoding='utf-8') as f:
        f.write(headerLEVES)
        for row in EmissCityLevesBR:
            f.write(', '.join(f'{value:.5f}' if isinstance(value, float) else f'{int(value)}' for value in row) + '\n')

    # Salvar os dados ano a ano (2013 a 2018)
    anos_desejados = range(2013, 2019)
    anos_coluna = EmissCityLevesBR[:, 0]

    for ano in anos_desejados:
        dados_ano = EmissCityLevesBR[anos_coluna == ano]
        print(f'Salvando os Dados de Emissao dos Leves {ano} por cidade (.txt)')

        file_ano = output_path / f'EmissCityLeves_BRAVES_{ano}.txt'
        with file_ano.open('w', encoding='utf-8') as f:
            f.write(headerLEVES)
            for row in dados_ano:
                f.write(', '.join(f'{value:.5f}' if isinstance(value, float) else f'{int(value)}' for value in row) + '\n')
                
    
    #-------------------------------MOTOCICLETAS-----------------------------
    
    headerMOTOS = ('YEAR_DATA, UF_CODE, MUN_CODE, EmissMotosCO, ' 
                      'EmissMotosHC, EmissMotosNMHCescape, '
                      'EmissMotosCH4, EmissMotosNOx, '
                      'EmissMotosRCHO, EmissMotosMP, EmissMotosCO2, '
                      'EmissMotosN2O, EmissMotosSO2, '
                      'EmissMotosNMHCabastece, EmissMotosCO2eq, '
                      'EmissMotosMP10pneu_freio, EmissMotosMP10pista, '
                      'EmissMotosMP10Ressuspensao, EmissMotosNMHCDiurnal, '
                      'EmissMotosNMHCHotSoak, EmissMotosNMHCRunningL')

    # Arquivo geral
    print('Salvando os Dados de Emissao das Motos por cidade (.txt)')
    all_file = output_path / 'EmissCityMotos_BRAVES.txt'
    with all_file.open('w', encoding='utf-8') as f:
        f.write(headerMOTOS)
        for row in EmissCityMotosBR:
            f.write(', '.join(f'{value:.5f}' if isinstance(value, float) else f'{int(value)}' for value in row) + '\n')

    # Dados por ano
    anos_desejados = np.unique(EmissCityMotosBR[:, 0]).astype(int)

    for ano in anos_desejados:
        print(f'Salvando os Dados de Emissao das Motos {ano} por cidade (.txt)')
        dados_ano = EmissCityMotosBR[EmissCityMotosBR[:, 0] == ano]

        file_ano = output_path / f'EmissCityMotos_BRAVES_{ano}.txt'
        with file_ano.open('w', encoding='utf-8') as f:
            f.write(headerMOTOS)
            for row in dados_ano:
                f.write(', '.join(f'{value:.5f}' if isinstance(value, float) else f'{int(value)}' for value in row) + '\n')
                
    
    #-------------------------------VEICULOS PESADOS----------------------------
    
    
    headerPESADOS = ('YEAR_DATA, UF_CODE, MUN_CODE, EmissPesadosCO,' 
                      'EmissPesadosHC, EmissPesadosNMHCescape, '
                      'EmissPesadosCH4, EmissPesadosNOx, '
                      'EmissPesadosRCHO, EmissPesadosMP, EmissPesadosCO2, '
                      'EmissPesadosN2O, EmissPesadosSO2, '
                      'EmissPesadosNMHCabastece, EmissPesadosCO2eq, '
                      'EmissPesadosMP10pneu_freio, EmissPesadosMP10pista, '
                      'EmissPesadosMP10Ressuspensao, EmissPesadosNMHCDiurnal, '
                      'EmissPesadosNMHCHotSoak, EmissPesadosNMHCRunningL') 

    # Arquivo geral
    print('Salvando os Dados de Emissao dos Pesados por cidade (.txt)')
    all_file = output_path / 'EmissCityPesados_BRAVES.txt'
    with all_file.open('w', encoding='utf-8') as f:
        f.write(headerPESADOS)
        for row in EmissCityPesadosBR:
            f.write(', '.join(f'{value:.5f}' if isinstance(value, float) else f'{int(value)}' for value in row) + '\n')

    # Dados por ano
    anos_desejados = np.unique(EmissCityPesadosBR[:, 0]).astype(int)

    for ano in anos_desejados:
        print(f'Salvando os Dados de Emissao dos Pesados {ano} por cidade (.txt)')
        dados_ano = EmissCityPesadosBR[EmissCityPesadosBR[:, 0] == ano]

        file_ano = output_path / f'EmissCityPesados_BRAVES_{ano}.txt'
        with file_ano.open('w', encoding='utf-8') as f:
            f.write(headerPESADOS)
            for row in dados_ano:
                f.write(', '.join(f'{value:.5f}' if isinstance(value, float) else f'{int(value)}' for value in row) + '\n')
                
                
                
    # Zera algumas colunas específicas
    EmissCityMotosBR[:, 8] = 0                     
    EmissCityPesadosBR[:, 8] = 0                  
    EmissCityPesadosBR[:, 13] = 0                 
    EmissCityPesadosBR[:, 18:21] = 0              
    
    """Soma das emissões por categoria, mantendo as 3 primeiras colunas
    (ano, UF, município)"""
    EMISSAOtotal_BR = np.hstack([
        EmissCityLevesBR[:, :3],  # colunas 1–3
        EmissCityLevesBR[:, 3:] +
        EmissCityComLevesBR[:, 3:] +
        EmissCityMotosBR[:, 3:] +
        EmissCityPesadosBR[:, 3:]
    ])
    
    # Conversão das emissões de gramas para toneladas
    EMISSAOtotal_BR[:, 3:] = EMISSAOtotal_BR[:, 3:] / 1_000_000
    
    
    headersTOTAL = [
    'YEAR_DATA', 'UF_CODE', 'MUN_CODE', 'EmissCO', 'EmissHC', 'EmissNMHCescape',
    'EmissCH4', 'EmissNOx', 'EmissRCHO', 'EmissMP', 'EmissCO2', 'EmissN2O',
    'EmissSO2', 'EmissNMHCabastece', 'EmissCO2eq', 'EmissMP10pneu_freio',
    'EmissMP10pista', 'EmissMP10Ressuspensao', 'EmissNMHCDiurnal',
    'EmissNMHCHotSoak', 'EmissNMHCRunningL'
    ]
    
    # Converte a matriz NumPy para DataFrame
    df_total = pd.DataFrame(EMISSAOtotal_BR, columns=headersTOTAL)
    
    # Salva o arquivo total
    print('Salvando os Dados de Emissão TOTAL NO BRASIL por cidade (.txt)')
    arquivo_total = output_path / 'EmissCityTOTAL_BRAVES.txt'
    df_total.to_csv(arquivo_total, sep=',', index=False, float_format='%.5f')
    
    # Lista e ordena os anos únicos
    anos = np.sort(df_total['YEAR_DATA'].unique())
    
    # Salva arquivos por ano
    for ano in anos:
        print(f'Salvando os Dados de Emissão TOTAL {int(ano)} por cidade (.txt)')
        df_ano = df_total[df_total['YEAR_DATA'] == ano]
        
        arquivo_ano = output_path / f'EmissCityTOTAL_BRAVES_{int(ano)}.txt'
        df_ano.to_csv(arquivo_ano, sep=',', index=False, float_format='%.5f')