#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr 28 13:25:21 2025

@author: brunojalowski
"""

import pandas as pd

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
peso_motos =  0.3  #temporário
peso_pesados = 16.0 

df['peso_medio'] = (df.loc[:,'leves'] * peso_leves +
                    df.loc[:,'motocicletas'] * peso_motos +
                    df.loc[:,'pesados'] * peso_pesados) / df.loc[:,'TOTAL']


##FALTA ASSOCIAR GEOGRAFICAMENTE,POIS CADA LINHA É UMA CIDADE