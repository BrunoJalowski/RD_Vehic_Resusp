#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 30 17:17:14 2025

@author: brunojalowski
"""
import pandas as pd
import numpy as np
from pathlib import Path


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
    
 





    #--------------------------------COMERCIAIS LEVES-------------------------
    print("***ESTIMANDO AS EMISSÕES DE SO2 PARA OS VEÍCULOS COMERCIAIS LEVES - BR***")

    # Caminho para o arquivo Excel
    filename = Path(EF_Folder) / 'EF_SO2_Pollutant' / 'EF_LightCommercial_SO2.xlsx'
    
    # Lê o arquivo Excel (descarta a primeira linha após leitura)
    df_raw = pd.read_excel(filename)
    df_raw = df_raw.iloc[1:]  # remove a primeira linha
    
    TiposdeCombustivel = [
         ['GASOLINA', 1],
         ['ALCOOL', 2],
         ['FLEX GASOLINA', 3],
         ['FLEX ETANOL', 4],
         ['DIESEL', 5]
     ]

    TiposdeCombustivel_dict = {row[0]: row[1] for row in TiposdeCombustivel}
    
    # Função auxiliar para mapear nome → código
    def mapear_codigo_combustivel(nome_combustivel):
        nome_formatado = nome_combustivel.strip().upper()
        if nome_formatado == 'GASOLINA':
            return TiposdeCombustivel_dict['GASOLINA']
        elif nome_formatado == 'ETANOL':
            return TiposdeCombustivel_dict['ALCOOL']
        elif nome_formatado == 'FLEX GASOLINA':
            return TiposdeCombustivel_dict['FLEX GASOLINA']
        elif nome_formatado == 'FLEX ETANOL':
            return TiposdeCombustivel_dict['FLEX ETANOL']
        elif nome_formatado == 'DIESEL':
            return TiposdeCombustivel_dict['DIESEL']
        else:
            return np.nan  # ou lançar erro
    
    # Aplica o mapeamento à coluna do combustível (assumindo que é a 2ª coluna)
    df_raw.iloc[:, 1] = df_raw.iloc[:, 1].apply(mapear_codigo_combustivel)
    
    # Converte para NumPy se necessário
    num = df_raw.select_dtypes(include=[np.number]).to_numpy()
    
    # Criando anos faltantes
    anosfaltantes = np.arange(np.min(MATRIZ_comLEVES.iloc[:, 3]), np.min(num[:, 0]) - 1)
    tamanho = len(anosfaltantes)
    anosfaltantes = np.sort(np.concatenate([anosfaltantes, anosfaltantes]))
    anosfaltantes = np.column_stack([anosfaltantes, np.tile(num[0, 1:], (tamanho, 1))])
    num = np.vstack([anosfaltantes, num])
    
    # ------------------------------------------------------------------------
    
    # Adicionando coluna para teor de enxofre
    MATRIZ_comLEVES['SO2'] = np.nan
    
    # Iterando sobre cada linha de 'num' para atribuir o teor de enxofre
    for ii in range(len(num)):
        print(f'***VEICULOS COMERCIAIS LEVES__SO2 - BR*** {ii+1}/{len(num)}')
        # Encontrando correspondências de ano e tipo de combustível
        matches = MATRIZ_comLEVES[
            (MATRIZ_comLEVES.iloc[:, 3] == num[ii, 0]) & (MATRIZ_comLEVES.iloc[:, 4] == num[ii, 1])
        ]
        # Atribuindo o valor de teor de enxofre
        MATRIZ_comLEVES.loc[matches.index, 'SO2'] = num[ii, 3]
    
    # Para veículos leves com combustível Gasolina (tipo 5) no ano de 2013 com teor 0.05
    cond1 = (
        (MATRIZ_comLEVES.iloc[:, 0] == 2013) &  # ano
        (MATRIZ_comLEVES.iloc[:, 4] == 5) &     # tipo de combustível
        (MATRIZ_comLEVES.iloc[:, -1] == 0.05)   # teor de enxofre
    )
    MATRIZ_comLEVES.loc[cond1, MATRIZ_comLEVES.columns[-1]] = 0.8
    
    # Para veículos leves FLEX Gasolina (tipo 4) no ano de 2013 com teor 0.05
    cond2 = (
        (MATRIZ_comLEVES.iloc[:, 0] == 2013) &
        (MATRIZ_comLEVES.iloc[:, 4] == 4) &
        (MATRIZ_comLEVES.iloc[:, -1] == 0.05)
    )
    MATRIZ_comLEVES.loc[cond2, MATRIZ_comLEVES.columns[-1]] = 0.8
    
    #--------------------------------------------------------------------------
    
    # O Calculo de Emissão de SO2 baseia-se na seguinte equação:
    emissoes_valor = (
        MATRIZ_comLEVES.iloc[:, 15] *
        MATRIZ_comLEVES.iloc[:, 16] *
        MATRIZ_comLEVES.iloc[:, 17] *
        MATRIZ_comLEVES.iloc[:, 18]
    )
    
    # Substituir NaNs por 0 no resultado da multiplicação
    emissoes_valor = emissoes_valor.fillna(0)
    
    # Concatenar com colunas 1 a 6
    EmissoesSO2 = pd.concat([MATRIZ_comLEVES.iloc[:, 0:6], emissoes_valor.rename("EmissaoSO2")], axis=1)
    
    # Agrupamento por cidade (ano, UF, município)
    EmissCityComLevesSO2 = EmissoesSO2.groupby([EmissoesSO2.columns[0], EmissoesSO2.columns[1], EmissoesSO2.columns[2]])["EmissaoSO2"].sum().reset_index()
    
    # Agrupamento por UF (ano, UF)
    EmissUFComLevesSO2 = EmissoesSO2.groupby([EmissoesSO2.columns[0], EmissoesSO2.columns[1]])["EmissaoSO2"].sum().reset_index()
        
    
    
    
    
    
    
    
    # -------------------------MOTOCICLETAS--------------------------
    print('***ESTIMANDO AS EMISSOES DE SO2 PARA AS MOTOCICLETAS - BR***')
    
    filename = EF_Folder + '\\EF_SO2_Pollutant\\EF_MotorCycle_SO2.xlsx'
    
    # Lê o arquivo Excel
    df = pd.read_excel(filename, header=None)
    
    # Remove a primeira linha (como no código MATLAB)
    df = df.iloc[1:]
    
    # Atribuindo o Código do tipo de Combustivel Gasolina
    df.iloc[:, 1] = df.iloc[:, 1].apply(mapear_codigo_combustivel)
    
    
    # ------------------------------------------------------------------------
    # Gerando anos faltantes
    anosfaltantes = np.arange(min(MATRIZ_MOTOS[:, 3]), min(df.iloc[:, 0]) - 1)
    tamanho = len(anosfaltantes)
    anosfaltantes = np.sort(np.concatenate([anosfaltantes, anosfaltantes]))
    anosfaltantes = np.column_stack([anosfaltantes, np.tile(df.iloc[:2, 1:].values, (tamanho, 1))])
    num = np.vstack([anosfaltantes, df.values])
    
    # ------------------------------------------------------------------------
    # Colocando os Valores de Teor de Enxofre para cada respectivo ano modelo e tipo de combustivel na MATRIZ_MOTOS.
    MATRIZ_MOTOS = np.hstack([MATRIZ_MOTOS, np.full((MATRIZ_MOTOS.shape[0], 1), np.nan)])
    
    for ii in range(len(num)):
        print(f'***MOTOCICLETAS__SO2 - BR*** {ii+1}/{len(num)}')
        
        # Encontrando os indices correspondentes
        cond = np.isin(MATRIZ_MOTOS[:, 3:5], num[ii, 0:2], axis=1)
        MATRIZ_MOTOS[cond, -1] = num[ii, 4]
    
    # ------------------------------------------------------------------------
    # PARA ESTIMATIVA DE SO2 NO ANO DE 2013
    # Para MOTOCICLETAS com tipo de combustivel Gasolina:
    cond1 = (MATRIZ_MOTOS[:, 0] == 2013) & (MATRIZ_MOTOS[:, 4] == 5) & (MATRIZ_MOTOS[:, -1] == 0.05)
    MATRIZ_MOTOS[cond1, -1] = 0.8
    
    # Para MOTOCICLETAS com tipo de combustivel FLEX Gasolina:
    cond2 = (MATRIZ_MOTOS[:, 0] == 2013) & (MATRIZ_MOTOS[:, 4] == 4) & (MATRIZ_MOTOS[:, -1] == 0.05)
    MATRIZ_MOTOS[cond2, -1] = 0.8
    
    # O Cálculo de Emissão de SO2 baseia-se na seguinte equação:
    emissoes_valor = (
        MATRIZ_MOTOS.iloc[:, 15] *
        MATRIZ_MOTOS.iloc[:, 16] *
        MATRIZ_MOTOS.iloc[:, 17] *
        MATRIZ_MOTOS.iloc[:, 18] *
        MATRIZ_MOTOS.iloc[:, 19]
    )
    
    # Substituir NaNs por 0 no resultado da multiplicação
    emissoes_valor = emissoes_valor.fillna(0)
    
    # Concatenar com as colunas 1 a 6
    EmissoesSO2 = pd.concat([MATRIZ_MOTOS.iloc[:, 0:6], emissoes_valor.rename("EmissaoSO2")], axis=1)
    
    # Agrupamento por cidade (ano, UF, município)
    EmissCityMotosSO2 = EmissoesSO2.groupby([EmissoesSO2.columns[0], EmissoesSO2.columns[1], EmissoesSO2.columns[2]])["EmissaoSO2"].sum().reset_index()
    
    # Agrupamento por UF (ano, UF)
    EmissUFMotosSO2 = EmissoesSO2.groupby([EmissoesSO2.columns[0], EmissoesSO2.columns[1]])["EmissaoSO2"].sum().reset_index()
    
    
    
    
    
    
    
    # ----------------------VEÍCULOS PESADOS-----------------------
    print("***ESTIMANDO AS EMISSÕES DE SO2 PARA OS VEÍCULOS PESADOS - BR***")
    
    # Lendo o arquivo de dados
    filename = EF_Folder + '\\EF_SO2_Pollutant\\EF_HeavyDuty_SO2.xlsx'
    df = pd.read_excel(filename, header=None)
    
    # Remover a primeira linha (header)
    df = df.iloc[1:]
    
    # Atribuindo o Código do tipo de Combustível DIESEL
    codigoDIESEL = TiposdeCombustivel[TiposdeCombustivel[:, 0] == 'DIESEL', 1]
    df.loc[df[1] == 'Diesel', 1] = codigoDIESEL
    
    # ----------------------------------------------------------------------
    # Gerando anos faltantes
    anosfaltantes = np.arange(np.min(MATRIZ_PESADOS[:, 3]), np.min(df.iloc[:, 0]) - 1)
    tamanho = len(anosfaltantes)
    anosfaltantes = np.sort(np.concatenate([anosfaltantes, anosfaltantes]))
    anosfaltantes = np.column_stack([anosfaltantes, np.tile(df.iloc[:2, 1:].values, (tamanho, 1))])
    df = pd.concat([pd.DataFrame(anosfaltantes), df], ignore_index=True)
    
    # ----------------------------------------------------------------------
    # Colocando os valores de Teor de Enxofre para cada respectivo ano, modelo e tipo de combustível
    MATRIZ_PESADOS = np.hstack([MATRIZ_PESADOS, np.full((MATRIZ_PESADOS.shape[0], 1), np.nan)])
    
    for ii in range(len(df)):
        print(f"***VEÍCULOS PESADOS__SO2 - BR*** {ii+1}/{len(df)}")
        
        # Encontrando os índices correspondentes
        cond = np.isin(MATRIZ_PESADOS[:, 3:5], df.iloc[ii, 0:2].values, axis=1)
        MATRIZ_PESADOS[cond, -1] = df.iloc[ii, 4]
    
    # ----------------------------------------------------------------------
    # PARA ESTIMATIVA DE SO2 NO ANO DE 2013
    
    # Para veículos PESADOS com tipo de combustível Diesel:
    cond1 = (MATRIZ_PESADOS[:, 0] == 2013) & (MATRIZ_PESADOS[:, 4] == 2)  # código 2 para Diesel
    MATRIZ_PESADOS[cond1, -1] = 0.8
    
    # Para veículos PESADOS com tipo de combustível Diesel no ano de 2012:
    cond2 = (MATRIZ_PESADOS[:, 0] == 2013) & (MATRIZ_PESADOS[:, 3] == 2012) & (MATRIZ_PESADOS[:, 4] == 2)
    MATRIZ_PESADOS[cond2, -1] = 0.01
    
    # Para veículos PESADOS com tipo de combustível Diesel no ano de 2013:
    cond3 = (MATRIZ_PESADOS[:, 0] == 2013) & (MATRIZ_PESADOS[:, 3] == 2013) & (MATRIZ_PESADOS[:, 4] == 2)
    MATRIZ_PESADOS[cond3, -1] = 0.01
    
    # Para veículos PESADOS com tipo de combustível Diesel no ano de 2014:
    cond4 = (MATRIZ_PESADOS[:, 0] == 2013) & (MATRIZ_PESADOS[:, 3] == 2014) & (MATRIZ_PESADOS[:, 4] == 2)
    MATRIZ_PESADOS[cond4, -1] = 0.01
        
    # O Cálculo de Emissão de SO2 baseia-se na seguinte equação:
    emissoes_valor = (
        MATRIZ_PESADOS.iloc[:, 14] *  # col 15 em MATLAB
        MATRIZ_PESADOS.iloc[:, 15] *  # col 16
        MATRIZ_PESADOS.iloc[:, 16] *  # col 17
        MATRIZ_PESADOS.iloc[:, 17]    # col 18
    )
    
    # Substituir NaNs por 0 no resultado da multiplicação
    emissoes_valor = emissoes_valor.fillna(0)
    
    # Concatenar com as colunas 1 a 6
    EmissoesSO2 = pd.concat([MATRIZ_PESADOS.iloc[:, 0:6], emissoes_valor.rename("EmissaoSO2")], axis=1)
    
    # Agrupamento por cidade (ano, UF, município)
    EmissCityPesadosSO2 = EmissoesSO2.groupby(
        [EmissoesSO2.columns[0], EmissoesSO2.columns[1], EmissoesSO2.columns[2]]
    )["EmissaoSO2"].sum().reset_index()
    
    # Agrupamento por UF (ano, UF)
    EmissUFPesadosSO2 = EmissoesSO2.groupby(
        [EmissoesSO2.columns[0], EmissoesSO2.columns[1]]
    )["EmissaoSO2"].sum().reset_index()
    
    
    return EmissCityLevesSO2, EmissCityComLevesSO2, EmissCityMotosSO2, EmissCityPesadosSO2