import geopandas as gpd
import pandas as pd
import numpy as np
from concurrent.futures import ProcessPoolExecutor

"""
Totalmente ChatGPT - Igor T.
"""

# ==========================================================
# 🔹 Função auxiliar — corte com sjoin e interseção
# ==========================================================
def intersect_by_sjoin(gdf_left, gdf_right):
    """
    Realiza a interseção entre dois GeoDataFrames de forma equivalente
    a gpd.overlay(..., how='intersection'), mas mais performática.

    Usa sjoin para identificar pares espaciais e calcula interseções
    somente nesses pares.

    Os índices originais de cada GeoDataFrame são preservados como:
        'index_left' e 'index_right'

    Parameters
    ----------
    gdf_left : GeoDataFrame
        Primeiro GeoDataFrame (ex.: estradas).
    gdf_right : GeoDataFrame
        Segundo GeoDataFrame (ex.: municípios).

    Returns
    -------
    GeoDataFrame
        Geometrias resultantes da interseção com colunas:
        ['index_left', 'index_right', 'geometry']
    """

    # Garante que CRS é igual
    if gdf_left.crs != gdf_right.crs:
        gdf_right = gdf_right.to_crs(gdf_left.crs)

    # sjoin para pares espaciais
    joined = gpd.sjoin(
        gdf_left, gdf_right[['geometry']],
        how='inner', predicate='intersects'
    )

    if joined.empty:
        return gpd.GeoDataFrame()

    gdf_left_to_intersect = gdf_left.loc[
        joined.index, 'geometry'].reset_index(drop=True)
    gdf_right_to_intersect = gdf_right.loc[
        joined['index_right'], 'geometry'].reset_index(drop=True)


    # Calcula interseção apenas para pares que se tocam
    # Usa apply porque cada linha refere-se a uma combinação (left-right)
    # joined['geometry'] = joined.apply(
    #     lambda row: row.geometry.intersection(gdf_right.loc[row['index_right'], 'geometry']),
    #     axis=1
    # )

    inter_geom = gdf_left_to_intersect.reset_index(
        drop=True).intersection(
            gdf_right_to_intersect.reset_index(drop=True)
    )

    # Remove geometrias vazias
    joined = joined.reset_index(drop=False).rename(
        columns={'index': 'index_left'})
    joined.loc[:, 'geometry'] = inter_geom

    joined = gpd.GeoDataFrame(joined, geometry='geometry', crs=gdf_left.crs)

    joined = joined.loc[~joined.geometry.is_empty].reset_index(drop=True)

    # GeoDataFrame com índices originais preservados
    joined = gpd.GeoDataFrame(
        joined[['index_left', 'index_right', 'geometry']],
        geometry='geometry',
        crs=gdf_left.crs
    )

    # Fazendo o merge dos parâmetros dos dois geodataframes
    return gpd.GeoDataFrame(
        pd.merge(
            pd.merge(
                joined,
                gdf_left.drop(columns='geometry'),
                left_on='index_left',
                right_index=True
            ),
            gdf_right.drop(columns='geometry'),
            left_on='index_right',
            right_index=True
        )
    ).drop(columns=['index_left', 'index_right'])

# ==========================================================
# 🔹 Função paralelizada
# ==========================================================
# def _intersect_chunk(chunk, gdf_left):
#     """Função auxiliar usada em paralelo."""
#     sub_join = gpd.sjoin(
#         gdf_left, chunk[['geometry']],
#         how='inner', predicate='intersects'
#     )
#     sub_join['geometry'] = sub_join.apply(
#         lambda row: row.geometry.intersection(chunk.loc[
#             row['index_right'], 'geometry']),
#         axis=1
#     )
#     sub_join = sub_join.loc[~sub_join.geometry.is_empty].reset_index(drop=True)
#     return sub_join[['index_left', 'index_right', 'geometry']]


def intersect_by_sjoin_parallel(gdf_left, gdf_right, n_jobs=4):
    """
    Versão paralelizada do intersect_by_sjoin.

    Divide gdf_right em blocos e processa cada bloco em paralelo.

    Parameters
    ----------
    gdf_left : GeoDataFrame
        GeoDataFrame base (ex.: estradas).
    gdf_right : GeoDataFrame
        GeoDataFrame com o qual será feita a interseção (ex.: municípios).
    n_jobs : int, optional
        Número de processos paralelos (default 4).

    Returns
    -------
    GeoDataFrame
        Geometrias resultantes da interseção com colunas:
        ['index_left', 'index_right', 'geometry']
    """

    if gdf_left.crs != gdf_right.crs:
        gdf_right = gdf_right.to_crs(gdf_left.crs)

    # Divide o gdf_right em blocos equilibrados
    chunks = np.array_split(gdf_right, n_jobs)

    # Executa em paralelo
    with ProcessPoolExecutor(max_workers=n_jobs) as executor:
        results = list(executor.map(
            intersect_by_sjoin, chunks, [gdf_left]*n_jobs))

    # Combina resultados
    result = pd.concat(results, ignore_index=True)
    return gpd.GeoDataFrame(result, geometry='geometry', crs=gdf_left.crs)
