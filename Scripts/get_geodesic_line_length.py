#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Oct 16 16:13:53 2025

@author: brunojalowski
"""
from shapely.geometry import LineString, MultiLineString, Point
from pyproj import Geod
import numpy as np


def get_geodesic_line_length(
        geom: LineString | MultiLineString,
        geod: Geod) -> float:
    """Calculates geodesic length.

    Parameters
    ----------
    gdf : gpd.GeoDataFrame
        Road lengths.
    geod: Geod
        The geoid to consider.

    Returns
    -------
    float
        The lenght.
    """
    if geom is None or geom.is_empty:
        return 0.0

    # LineString direto
    if isinstance(geom, LineString):
        xs, ys = zip(*geom.coords)  # lon, lat
        # Usa método C acelerado se disponível
        try:
            return float(geod.line_length(xs, ys))
        except AttributeError:
            # fallback: inv entre pares consecutivos (pyproj.Geod.inv é vectorizado)
            lons = np.asarray(xs)
            lats = np.asarray(ys)
            if lons.size < 2:
                return 0.0
            az12, az21, dist = geod.inv(lons[:-1], lats[:-1], lons[1:], lats[1:])
            return float(np.sum(dist))

    # geod: Geod# MultiLineString: some os comprimentos das geometrias internas
    if isinstance(geom, MultiLineString):
        total = 0.0
        for part in geom.geoms:
            total += get_geodesic_line_length(part, geod)
        return total
    
    if isinstance(geom, Point):
        return 0.0
    
    raise NotImplementedError(
        f'Not implemented for that geometry: {type(geom)}')