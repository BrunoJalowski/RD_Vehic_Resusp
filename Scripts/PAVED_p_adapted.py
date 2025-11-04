#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Oct 31 19:01:46 2025

@author: brunojalowski
"""
import numpy as np

def creditsf_vectorized(ISRAIN, HSP, max_hours_since_precip=12):
    """
    Versão vetorizada de creditsf.
    
    Parameters:
        ISRAIN : np.ndarray
            Boolean array (time, pixels)
        HSP : np.ndarray
            Hours since precipitation (time, pixels)
        max_hours_since_precip : int
            Limite máximo de horas para crédito
    
    Returns:
        credits : np.ndarray
            Mitigation credits, mesmo shape de ISRAIN/HSP
    """
    # Inicializa credits
    credits = ISRAIN.astype(int)
    
    # aplica limite de horas
    mask = (HSP <= max_hours_since_precip)
    
    # acumulado por pixel ao longo do tempo
    credits_cum = np.zeros_like(credits)
    credits_cum[0, :] = credits[0, :]
    
    for t in range(1, ISRAIN.shape[0]):
        credits_cum[t, :] = np.where(mask[t, :],
                                     credits[t, :] + credits_cum[t-1, :],
                                     credits[t, :])
    return credits_cum * 0.2



def nmf_vectorized(rain, threshold=0.0254):
    """
    Versão vetorizada do cálculo do NMF para um array 3D (time, ny, nx).
    
    Parameters:
        rain : np.ndarray
            Array 3D com precipitação horária (time, ny, nx)
        threshold : float
            Limite mínimo de chuva para mitigação natural
            
    Returns:
        nat_mit_factor : np.ndarray
            Array 3D com o fator de mitigação natural
    """
    time, ny, nx = rain.shape
    rain_flat = rain.reshape(time, -1)  # transforma em (time, pixels)
    
    # máscara de chuva
    israin = rain_flat > threshold
    
    # caso não haja chuva
    if not israin.any():
        return np.ones_like(rain, dtype='f')
    
    # fator inicial
    nat_mit_factor = 1 - 1.2 * israin
    
    # horas desde a última chuva
    idx = np.arange(time)[:, None]
    last_rain = np.where(israin, idx, -np.inf)
    hours_since_rain = idx - np.maximum.accumulate(last_rain, axis=0)
    
    # créditos e débitos
    credits = np.round(creditsf_vectorized(israin, hours_since_rain), 1)
    debits = np.round(hours_since_rain * 0.2, 1)
    
    debit_eligible = ~israin
    mask = debit_eligible & (credits >= debits)
    nat_mit_factor[mask] -= 0.2
    
    # limitar para >= 0
    nat_mit_factor = np.maximum(nat_mit_factor, 0)
    
    return nat_mit_factor.reshape(time, ny, nx)