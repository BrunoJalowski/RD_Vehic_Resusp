#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr 22 08:39:53 2025

@author: brunojalowski
"""
import pandas as pd
import numpy as np
from pathlib import Path
from EmissoesEvaporativasv10_201901_adicionar_motos import anos_dados, valores_suc

path = Path('/home/brunojalowski/Downloads/emissoes_evaporativas_diurnal_hot_runningV2')

#%% Importando arquivo com os dados de FATORES DE DETERIORAÇÃO
# LEITURA DO ARQUIVO
print("Reading FATORES DE DETERIORAÇÃO automóveis, comerciais leves e motos")
filenameDL = path / 'Fatores_Deterioracao_Leves.xlsx'
rawDL = pd.read_excel(filenameDL)
numDL = rawDL.select_dtypes(include='number').to_numpy()

  
#LEITURA DO ARQUIVO
print('Reading FATORES DE DETERIORAÇÃO Veículos Pesados')
filenameDP = path / 'Fatores_Deterioracao_Pesados.xlsx'
rawDP = pd.read_excel(filenameDP)
numDP = rawDP.select_dtypes(include='number').to_numpy()

#LEITURA DO ARQUIVO
print('Reading FATORES DE DETERIORAÇÃO MOTOCICLETAS')
filenameDM = path / 'Fatores_Deterioracao_Motos.xlsx'
rawDM = pd.read_excel(filenameDM)
numDM = rawDM.select_dtypes(include='number').to_numpy()

#%% Filtra dados de Ano, Ano Modelo e calcula a idade de cada modelo
Anos_deterioracao = []

for ano in [2019]:
    df = valores_suc[valores_suc.iloc[:, 0] == ano].iloc[:, :2]
    nova_coluna = ano - df.iloc[:, 1] + 1
    combinado = np.column_stack((df.to_numpy(), nova_coluna.to_numpy()))
    Anos_deterioracao.append(combinado)

Anos_deterioracao = np.vstack(Anos_deterioracao)
    
#%% Adiciona valores de numDL, numDP e numDM em cada ano em um bloco final
n_linhas = Anos_deterioracao.shape[0]

DeterLevesOtto = np.hstack([Anos_deterioracao,
                            np.tile(numDL[1, :], (n_linhas, 1))])
DeterLevesDiesel = np.hstack([Anos_deterioracao,
                              np.tile(numDL[0, :], (n_linhas, 1))])
DeterPesados = np.hstack([Anos_deterioracao,
                          np.tile(numDP[0, :], (n_linhas, 1))])
DeterMotosOtto = np.hstack([Anos_deterioracao,
                            np.tile(numDM[0, :], (n_linhas, 1))])

#%%
""" Como a nossa estimativa está limitada à vida útil dos veículos por 40 
anos, quando a idade do ano modelo for superior a 40 aplicaremos 0 ao seu
fator de deterioração """

DeterLevesOtto[DeterLevesOtto[:, 2] > 40, 3:] = 0
DeterLevesDiesel[DeterLevesDiesel[:, 2] > 40, 3:] = 0
DeterPesados[DeterPesados[:, 2] > 40, 3:] = 0
DeterMotosOtto[DeterMotosOtto[:, 2] > 40, 3:] = 0

#%%
"""Os veículos com idade menor ou igual a 5 anos de uso não serão
multiplicados os fatores de deterioração. Logo o seu valor será 1. Isso
para que quando multiplicar o fator de deterioração multiplique por ele
mesmo."""

DeterLevesOtto[DeterLevesOtto[:,2] <= 5, 3:] = 1
DeterLevesDiesel[DeterLevesDiesel[:,2] <= 5, 3:] = 1
DeterPesados[DeterPesados[:,2] <= 5, 3:] = 1
DeterMotosOtto[DeterMotosOtto[:,2] <= 5, 3:] = 1

#%%
"""Agora devemos considerar o acúmulo de Rodagem para aplicar o Fator de
Deterioração."""

# Inicializando variáveis
IdadeMaximaVeic = np.sort(pd.unique(Anos_deterioracao[:,2]))
fator = 0  #fator de deterioração acumulado
mm = 0

# Criando o DataFrame com o número de linhas correspondente ao tamanho de IdadeMaximaVeic
FdeterIDADE = pd.DataFrame(np.zeros((len(IdadeMaximaVeic), 2)), columns=[0,1])

#%% Fator de deterioração crescente com base na idade máxima dos veículos
for ii in range(len(IdadeMaximaVeic)):  
    jj = ii - mm
    if jj > 5:
        if fator < 3:
            fator += 1
            mm = ii - 1 
        else:
            fator = 3
    FdeterIDADE.iloc[ii] = [IdadeMaximaVeic[ii], fator]

# Substitui os valores 0 na segunda coluna por 1
FdeterIDADE.loc[FdeterIDADE.iloc[:, 1] == 0, 1] = 1
    
#%%
"""Fazendo a multipicação dos fatores de deterioração pelo acúmulo de vezes
que o ano modelo completou 5 anos de uso."""

for kk in range(len(IdadeMaximaVeic)): 
    lia = DeterLevesDiesel[:, 2] == IdadeMaximaVeic[kk]
    DeterLevesDiesel[lia, 3:] = np.power(DeterLevesDiesel[lia, 3:], FdeterIDADE.iloc[kk, 1])
    DeterLevesOtto[lia, 3:] = np.power(DeterLevesOtto[lia, 3:], FdeterIDADE.iloc[kk, 1])
    DeterPesados[lia, 3:] = np.power(DeterPesados[lia, 3:], FdeterIDADE.iloc[kk, 1])
    DeterMotosOtto[lia, 3:] = np.power(DeterMotosOtto[lia, 3:], FdeterIDADE.iloc[kk, 1])









#%%
def FatorDETERIORACAO5(path, valores_suc, Ano_unico2):
    # Importando arquivo com os dados de FATORES DE DETERIORAÇÃO
    # LEITURA DO ARQUIVO
    print("Reading FATORES DE DETERIORAÇÃO automóveis, comerciais leves e motos")
    filenameDL = path / 'Fatores_Deterioracao_Leves.xlsx'
    rawDL = pd.read_excel(filenameDL)
    numDL = rawDL.select_dtypes(include='number').to_numpy()
    
      
    #LEITURA DO ARQUIVO
    print('Reading FATORES DE DETERIORAÇÃO Veículos Pesados')
    filenameDP = path / 'Fatores_Deterioracao_Pesados.xlsx'
    rawDP = pd.read_excel(filenameDP)
    numDP = rawDP.select_dtypes(include='number').to_numpy()
    
    #LEITURA DO ARQUIVO
    print('Reading FATORES DE DETERIORAÇÃO MOTOCICLETAS')
    filenameDM = path / 'Fatores_Deterioracao_Motos.xlsx'
    rawDM = pd.read_excel(filenameDM)
    numDM = rawDM.select_dtypes(include='number').to_numpy()
         
    # Filtra dados de Ano, Ano Modelo e calcula a idade de cada modelo
    Anos_deterioracao = []

    for ano in [2019]:
        df = valores_suc[valores_suc.iloc[:, 0] == ano].iloc[:, :2]
        nova_coluna = ano - df.iloc[:, 1] + 1
        combinado = np.column_stack((df.to_numpy(), nova_coluna.to_numpy()))
        Anos_deterioracao.append(combinado)

    Anos_deterioracao = np.vstack(Anos_deterioracao)
      
    
    # Adiciona valores de numDL, numDP e numDM em cada ano em um bloco final
    n_linhas = Anos_deterioracao.shape[0]

    DeterLevesOtto = np.hstack([Anos_deterioracao,
                                np.tile(numDL[1, :], (n_linhas, 1))])
    DeterLevesDiesel = np.hstack([Anos_deterioracao,
                                  np.tile(numDL[0, :], (n_linhas, 1))])
    DeterPesados = np.hstack([Anos_deterioracao,
                              np.tile(numDP[0, :], (n_linhas, 1))])
    DeterMotosOtto = np.hstack([Anos_deterioracao,
                                np.tile(numDM[0, :], (n_linhas, 1))])

    
    """ Como a nossa estimativa está limitada à vida útil dos veículos por 40 
    anos, quando a idade do ano modelo for superior a 40 aplicaremos 0 ao seu
    fator de deterioração """

    DeterLevesOtto[DeterLevesOtto[:, 2] > 40, 3:] = 0
    DeterLevesDiesel[DeterLevesDiesel[:, 2] > 40, 3:] = 0
    DeterPesados[DeterPesados[:, 2] > 40, 3:] = 0
    DeterMotosOtto[DeterMotosOtto[:, 2] > 40, 3:] = 0

    """Os veículos com idade menor ou igual a 5 anos de uso não serão
    multiplicados os fatores de deterioração. Logo o seu valor será 1. Isso
    para que quando multiplicar o fator de deterioração multiplique por ele
    mesmo."""

    DeterLevesOtto[DeterLevesOtto[:,2] <= 5, 3:] = 1
    DeterLevesDiesel[DeterLevesDiesel[:,2] <= 5, 3:] = 1
    DeterPesados[DeterPesados[:,2] <= 5, 3:] = 1
    DeterMotosOtto[DeterMotosOtto[:,2] <= 5, 3:] = 1

    """Agora devemos considerar o acúmulo de Rodagem para aplicar o Fator de
    Deterioração."""

    # Inicializando variáveis
    IdadeMaximaVeic = np.sort(pd.unique(Anos_deterioracao[:,2]))
    fator = 0  #fator de deterioração acumulado
    mm = 0

    # Criando o DataFrame com o número de linhas correspondente ao tamanho de IdadeMaximaVeic
    FdeterIDADE = pd.DataFrame(np.zeros((len(IdadeMaximaVeic), 2)), columns=[0,1])

    # Fator de deterioração crescente com base na idade máxima dos veículos
    for ii in range(len(IdadeMaximaVeic)):  
        jj = ii - mm
        if jj > 5:
            if fator < 3:
                fator += 1
                mm = ii - 1 
            else:
                fator = 3
        FdeterIDADE.iloc[ii] = [IdadeMaximaVeic[ii], fator]

    # Substitui os valores 0 na segunda coluna por 1
    FdeterIDADE.loc[FdeterIDADE.iloc[:, 1] == 0, 1] = 1
        
    """Fazendo a multipicação dos fatores de deterioração pelo acúmulo de vezes
    que o ano modelo completou 5 anos de uso."""

    for kk in range(len(IdadeMaximaVeic)): 
        lia = DeterLevesDiesel[:, 2] == IdadeMaximaVeic[kk]
        DeterLevesDiesel[lia, 3:] = np.power(DeterLevesDiesel[lia, 3:], FdeterIDADE.iloc[kk, 1])
        DeterLevesOtto[lia, 3:] = np.power(DeterLevesOtto[lia, 3:], FdeterIDADE.iloc[kk, 1])
        DeterPesados[lia, 3:] = np.power(DeterPesados[lia, 3:], FdeterIDADE.iloc[kk, 1])
        DeterMotosOtto[lia, 3:] = np.power(DeterMotosOtto[lia, 3:], FdeterIDADE.iloc[kk, 1])

    

    return DeterLevesDiesel, DeterLevesOtto, DeterMotosOtto, DeterPesados

