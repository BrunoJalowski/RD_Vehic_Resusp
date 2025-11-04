#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul  8 12:30:38 2025

@author: brunojalowski
"""
# %% Road surface reclassification

def reclassify_surface(gdf):
    """
    

    Parameters
    ----------
    gdf : TYPE
        DESCRIPTION.

    Returns
    -------
    gdf : TYPE
        DESCRIPTION.      
        
    """   
    paved = ['asphalt', 'paved', 'concrete', 'paving_stones', 'sett',
             'unhewn_cobblestone','concrete:plates', 'cobblestone',
             'wood','cobblestone:flattened','paving_stones:30',
             'metal','acrylic','concrete:lanes', 'artificial_turf',
             'paralepípedo','dett', 'seet', 'pavimentada', 'asphalt; paved',
             'Paralelepipedo', 'calçamento', 'yes', 'concrete, sett',
             'pedra_poliédrica', 'cobblestone;asphalt', 'metal;wood',
             'bitmac', 'asfalto,_paralelepípedo', 'parallelepiped',
             'cobblestone:lanes', 'bricks','Paralelepípedo','asphalt,paved',
             'stone', 'paved stones', 'unpaved; asphalt', 'pave_stones',
             'paralepípedos','paved;asphalt','Asfalto','Calçamento',
             'paving_stones;cobblestone', 'Madeira', 'concr',
             'grass_paver', 'Elevada_em_comcreto','paralelepipedo',
             'paralepipedos','paving_stones:20',
             'calçamento_octogonal_de_concreto_ascalho',
             'paving_stones; asphalt',
             'pedras_para_pavimentação',
             'bloquete','sertt',
             'paving_stones;asphalt','concrete:tiles','Paralelepípedos',
             'paved_with_rocks','asfalto2',
             'pavinentada','madeira','Piso_Intertravado',
             'paralelepípedo',
             'paving_stones:lanes','lane:concrete','pavimentado',
             'asfalto_e_paralelepípedo','piso_sextavado','pavimento',
             'cement','aett','concrete:blocks','paved; asphalt','Pavimento',
             'calcamento','Asfa','brick','paralé',
             'glass','pavimentado.',
             'calçada_(pedra_portuguesa)','iron','paver','block',
             'calçada_(pedra_irregular/arredondada)]','pavimentadoc']
    
    """ NOTAS
    - seet, dett são typos de sett
    - 
    """
    
    unpaved = [None, 'ground', 'unpaved', 'clay','dirt','gravel','compacted',
               'sand', 'earth', 'pebblestone', 'dirt;ground', 
               'asphalt;unpaved', 'Rua_Major_Manuel_Eduardo_de_Souza',
               'dirt/sand', '37280-000', 'fine_gravel', 'asphalt;dirt',
               'asphalt; asphalt; dirt','asphalt; dirt; asphalt', 'grass',
               'dirt;asphalt', 'terra', 'Pedras', 'Retorno', 'cascalho',
               'rock', 'dirt; unpaved; unpaved', 'GO-320','mud', 'saibro',
               'unpaved,_asphalt', 'Barro', 'unpaved; paved', 'plana',
               '1','ERS-137', 'Avenida_Presidente_Dutra', 'tartan',
               'asphalt;paved', 'asphalt; dirt','ground,sand','ground;sand',
               'não_pavimentada','Rua Rodolpho A. Felicetti', 'pedra',
               'Terra', 'asphalt_AND_DIRT','2','sand,ground',
               'Rua III;Rua Trinta e Dois','Rua_Tupã','uun',
               'unpaved;asphalt',
               'ground;paved',
               'paved;ground',
               'gt',
               'dirt; asphalt','Avenida Vitório Segundo Ben',
               'PLANE','survey',
               'paved;unpaved',
               'paved; unpaved',
               'unpaved; paved; unpaved','terra_batida',
               'unpaved;gravel;paved',
               'Viela_Inacio_Brites_de_Freitas','commercial',
               'dirt;sett','unapaved',
               'unpaved;gravel',
               'terrain',
               'Rua José Gonçalves Dias;Rua Duzentos e Vinte e Dois',
               'não_pavimentadoc','Cascalho',
               'Saibro',
               'IBGE',
               'nao_pavimentada','paving_stones;unpaved',
               'um','estrada',
               'trilha',
               'sem_pavimento','bare_rock','Rua Máximo',
               'paralelepípedo_e_sem_pavimentação',
               'asfalto,_paralelepídedo,_sem_pavimentação',
               'Rua João Paulo II',
               'soil','terra[','terrazzo',
               'Rua das Flores',
               'Rua Ibatinga',
               'Rua Nossa Senhora Aparecida',
               'sand; dirt; gravel',
               'o','[','semipavimentado',
               'hard',
               'Travessa_Jurema',
               'Pista_de_Pouso_e_Decolagem_Alegre',
               'grass;sand',
               'terr',
               'Terra/Barro','avenida_nossa_senhora_de_fátima',
               'surface',
               'rua_parceria_1025',
               'rocky',
               'no',
               'não_pavimentado',
               'Avenida_do_Bosque','Escadão_Rodoanel',
               'bing',
               'Estrada_de_Terra/Barro','unpaved111',
               'com',
               'unpavedBar_do_João',
               'i',
               'Não_Pavimentada',
               'dirtc',
               'compactes',
               'v',
               'n',
               'não_asfaltado',
               'grama',
               'footway',
               'compa','BOC-070','terra0','inte',
               'Piçarra',
               'unpaved; dirt','compac',
               'Unipaved',
               'dunas',
               'Trilha_do_Rio_Branco_(Marsilac_-_Itanhaém)',
               'us',
               'Córrego_do_Beija-Flor',
               'chipseal',
               'groundovertaking',
               'não_pa',
               'não_pavimentadow','woodchips',
               'rua_delibio_da_fontoura',
               'res',
               'estradas',
               'carpet','não_pavimentadoest',
               "un'",'unpaved=steep',
               'trilha_irregular',
               'em_obras',
               'não_pavimentado2','uy',
               'sand; dirt',
               'areia',
               'não_pavimentadocc',
               'travessa_capitão_jerónimo_silva',
               'co',
               '3ª_travessa_copacabana',
               'passarela_pernambuco',
               'passarela_paraiba',
               'passarela_alagoas',
               'Travessa_africa',
               'rua_barradão',
               'gr',
               'ground; asphalt','Travessa_Professor_Aída_Balaio',
               'não_pav',
               'não',
               'não_p',
               'asphalt; unpaved',
               '2w',
               'D',
               'gr[',
               'construction',
               'gate',
               'não_pavimentado3','nezpevněnýě',
               'buraco_do_cacique',
               'terra_batida2',
               'visinal_2',
               'cascalho_fino_em_alguns_pontos_areia',
               'terreno_natural',
               'unpaved036700',
               'cascalho_,terra_batida',
               'cascalho_e_terra',
               'esr','dir\\\\',
               'unpaved3']
    
    """ NOTAS
    - superfícies com mais de um tipo foram classificadas no pior
    - ERS-137 está sendo pavimentada ainda
    
    """
    
    # Reclassifying paved surfaces
    gdf.loc[gdf['surface'].isin(paved), 'surface'] = 'paved'
    
    # Reclassifying unpaved surfaces
    gdf.loc[(gdf['surface'].isin(unpaved)) |
            (gdf['surface'].isnull()), 'surface'] = 'unpaved'
    
    # Removing water surfaces from dataframe
    gdf.drop(labels=gdf.loc[gdf['surface'] == 'water'].index.tolist(),
             axis=0,
             inplace=True)
    
    return gdf
    
    


