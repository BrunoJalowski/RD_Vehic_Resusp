#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr 28 13:25:21 2025

@author: brunojalowski
"""

import pandas as pd
import geopandas as gpd
import numpy as np
import unidecode

path = '/home/brunojalowski/Downloads/emissoes_evaporativas_diurnal_hot_runningV2/2.FrotaPorMunicipio'
filename = f'{path}/frota_munic_modelo_janeiro_2019.xls'

df = pd.read_excel(filename, skiprows=3)

#%% Reclassificação categorias de veículos
"""
Classificação atual:
    Index(['UF', 'MUNICIPIO', 'TOTAL', 'AUTOMOVEL', 'BONDE', 'CAMINHAO',
           'CAMINHAO TRATOR', 'CAMINHONETE', 'CAMIONETA', 'CHASSI PLATAF',
           'CICLOMOTOR', 'MICRO-ONIBUS', 'MOTOCICLETA', 'MOTONETA', 'ONIBUS',
           'QUADRICICLO', 'REBOQUE', 'SEMI-REBOQUE', 'SIDE-CAR', 'OUTROS',
           'TRATOR ESTEI', 'TRATOR RODAS', 'TRICICLO', 'UTILITARIO'],
          dtype='object')

Reclassificação:
    leves = AUTOMOVEL, BONDE, CAMINHONETE, CAMIONETA, UTILITARIO, OUTROS
    motocicletas = CICLOMOTOR, MOTOCICLETA, MOTONETA, QUADRICICLO, SIDE-CAR, TRICICLO
    pesados = CAMINHAO, CAMINHAO TRATOR, CHASSI PLATAF, MICRO-ONIBUS, ONIBUS, REBOQUE,
            SEMI-REBOQUE, TRATOR ESTEI, TRATOR RODAS

"""

df['leves'] = df.loc[:, ['AUTOMOVEL',
                          'BONDE',
                          'CAMINHONETE',
                          'CAMIONETA',
                          'UTILITARIO',
                          'OUTROS']].sum(1)

df['motocicletas'] = df.loc[:, ['CICLOMOTOR',
                                'MOTOCICLETA',
                                'MOTONETA',
                                'QUADRICICLO',
                                'SIDE-CAR',
                                'TRICICLO']].sum(1)

df['pesados'] = df.loc[:, ['CAMINHAO',
                           'CAMINHAO TRATOR',
                           'CHASSI PLATAF',
                           'MICRO-ONIBUS',
                           'ONIBUS',
                           'REBOQUE',
                           'SEMI-REBOQUE',
                           'TRATOR ESTEI',
                           'TRATOR RODAS']].sum(1)

#%% Pesos das categorias de veículo (toneladas)

peso_leves =  1.1485  #temporário, ainda falta somar peso do motorista
peso_motos =  0.128
peso_pesados = 16.0 

df['peso_medio'] = (df.loc[:,'leves'] * peso_leves +
                    df.loc[:,'motocicletas'] * peso_motos +
                    df.loc[:,'pesados'] * peso_pesados) / df.loc[:,'TOTAL']

#%%

caminho_diretorio = r"/home/brunojalowski/Downloads/emissoes_evaporativas_diurnal_hot_runningV2"

def identificando_cod_ibge(caminho_diretorio):
    """
    Processa e extrai informações dos códigos do IBGE para estados e municípios 
    do Brasil

    Parâmetros:
    caminho_diretorio (str): Caminho do diretório onde estão localizados os arquivos

    Retorna:
        list[tuple]: Lista de tuplas contendo (nome do município, código do município IBGE).
        list[tuple]: Lista de tuplas contendo (nome do estado, código do estado IBGE).
        list[str]: Lista de siglas das unidades federativas (UF).
        numpy.ndarray: Array com os códigos numéricos das unidades federativas.
    """
    
    # Leitura do arquivo Excel
    filename = f'{caminho_diretorio}/RELATORIO_DTB_BRASIL_MUNICIPIO.xls'
    try:
        df = pd.read_excel(filename, skiprows=6)  # Pula as primeiras 6 linhas
    except Exception as e:
        print(f"Erro ao ler o arquivo Excel: {e}")
        return None, None, None, None
    
    # Renomeação das colunas
    df = df.rename(columns={
        'UF': 'cod_uf',
        'Nome_UF': 'nome_uf',
        'Código Município Completo': 'cod_municipio',
        'Nome_Município': 'nome_municipio'})
    
    # Criação da lista de municípios
    IBGE_CITIES = df[['cod_uf', 'nome_uf', 'cod_municipio', 'nome_municipio']].values.tolist()
    IBGE_CITIES_CODES = df['cod_municipio'].astype(str).values
    
    # Leitura do shapefile dos estados
    try:
        UFshp = gpd.read_file(f'{caminho_diretorio}/BR_UF_2023/BR_UF_2023.shp')
    except Exception as e:
        print(f"Erro ao ler o shapefile dos estados: {e}")
        return None, None, None, None
    
    # Extração de códigos e nomes dos estados
    codigos_uf = UFshp['CD_UF'].astype(int).values
    UFnames = UFshp['NM_UF'].values
    
    # Dicionário de mapeamento de códigos para siglas
    codigo_para_sigla = {
        11: 'RO', 12: 'AC', 13: 'AM', 14: 'RR', 15: 'PA', 16: 'AP', 17: 'TO',
        21: 'MA', 22: 'PI', 23: 'CE', 24: 'RN', 25: 'PB', 26: 'PE', 27: 'AL',
        28: 'SE', 29: 'BA', 31: 'MG', 32: 'ES', 33: 'RJ', 35: 'SP', 41: 'PR',
        42: 'SC', 43: 'RS', 50: 'MS', 51: 'MT', 52: 'GO', 53: 'DF'}
    
    # Gerar ibge_uf com base na ordem de codigos_uf
    ibge_uf = [codigo_para_sigla[codigo] for codigo in codigos_uf]
    
    # Leitura dos shapefiles dos municípios
    try:
        CITYshpIBGE = gpd.read_file(f'{caminho_diretorio}/BR_Municipios_2023/BR_Municipios_2023.shp')
    except Exception as e:
        print(f"Erro ao ler o shapefile dos municípios do IBGE: {e}")
        return None, None, None, None
    
    CITYcodesIBGE = CITYshpIBGE['CD_MUN'].astype(int).values
    CITYnamesIBGE = CITYshpIBGE['NM_MUN'].values
    
    try:
        CITYshpFOREST = gpd.read_file(f'{caminho_diretorio}/ForestGIS_Cidades_Brasil_pop2021_ibge/ForestGIS_Cidades_Brasil_pop2021_ibge.shp')
    except Exception as e:
        print(f"Erro ao ler o shapefile dos municípios do ForestGIS: {e}")
        return None, None, None, None
    
    CITYcodesFOREST = CITYshpFOREST['IBGECd'].astype(int).values
    CITYnamesFOREST = CITYshpFOREST['Nom_Mun'].values
    
    # Comparação de códigos entre diferentes fontes
    lia1 = np.isin(CITYcodesIBGE, IBGE_CITIES_CODES.astype(int))
    lia2 = np.isin(CITYcodesIBGE, CITYcodesFOREST)
    
    # Identificação de municípios faltantes
    Falta_Municipios = CITYnamesIBGE[~lia1]
    Falta_Codigo = CITYcodesIBGE[~lia1]
    
    # Correção de nomes de municípios faltantes
    Falta_Municipios = [unidecode(str(name)) for name in Falta_Municipios]
    
    # Adição de municípios faltantes na lista completa
    codiState = (Falta_Codigo // 10**5).astype(int)
    loccodes2 = np.searchsorted(codigos_uf, codiState)
    falta_codiState = UFnames[loccodes2]
    
    Municipios_faltantes = list(zip(falta_codiState, codiState, Falta_Codigo, Falta_Municipios))
    IBGE_CITIES.extend(Municipios_faltantes)
    
    # Ordenação da lista completa de municípios
    IBGE_CITIES.sort(key=lambda x: x[2])
    
    # Remoção de caracteres especiais e espaços
    CITYnames = [unidecode(str(city[3])).upper().replace(' ', '') for city in IBGE_CITIES]
    
    # Saída final
    ibge_dados_cidades = [(city[3], city[2], city[4]) for city in IBGE_CITIES]
    ibge_estados = list(zip(UFnames, codigos_uf))
    
    return ibge_dados_cidades, ibge_estados, ibge_uf, codigos_uf


ibge_dados_cidades, ibge_estados, ibge_uf, codigos_uf = identificando_cod_ibge(caminho_diretorio)

##FALTA ASSOCIAR GEOGRAFICAMENTE,POIS CADA LINHA É UMA CIDADE