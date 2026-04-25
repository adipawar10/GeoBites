"""
Haversine distance and buffer membership (numpy, no GIS deps).
"""
from __future__ import annotations

import numpy as np

EARTH_RADIUS_M = 6_371_000.0


def haversine_m(lat1: np.ndarray, lon1: np.ndarray, lat2: np.ndarray, lon2: np.ndarray) -> np.ndarray:
    """Pairwise distances from each (lat1,lon1) to each (lat2,lon2) broadcast last dim."""
    la1, lo1 = np.radians(lat1), np.radians(lon1)
    la2, lo2 = np.radians(lat2), np.radians(lon2)
    dlat = la2 - la1[..., None]
    dlon = lo2 - lo1[..., None]
    a = np.sin(dlat / 2) ** 2 + np.cos(la1[..., None]) * np.cos(la2) * np.sin(dlon / 2) ** 2
    c = 2 * np.arcsin(np.minimum(1.0, np.sqrt(a)))
    return EARTH_RADIUS_M * c


def min_distance_to_hubs(lat: np.ndarray, lon: np.ndarray, hub_lat: np.ndarray, hub_lon: np.ndarray) -> np.ndarray:
    """Min distance (meters) from each point to any hub."""
    d = haversine_m(lat, lon, hub_lat, hub_lon)
    return d.min(axis=1)
