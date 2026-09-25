"""Geospatial utilities and county boundary representations for Kenya."""

from typing import Optional
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
from agririsk.core.constants import KENYA_COUNTIES


def get_counties_geodataframe(target_crs: str = "EPSG:4326") -> gpd.GeoDataFrame:
    """Return a GeoDataFrame containing all 47 counties of Kenya with centroid points.

    Args:
        target_crs: Target coordinate reference system (defaults to EPSG:4326).

    Returns:
        GeoDataFrame with columns: code, name, asal_category, geometry (Point).
    """
    records = []
    for c in KENYA_COUNTIES:
        records.append({
            "county_code": c["code"],
            "county_name": c["name"],
            "asal_category": c["asal_category"],
            "latitude": c["lat"],
            "longitude": c["lon"],
            "geometry": Point(c["lon"], c["lat"])
        })

    gdf = gpd.GeoDataFrame(records, crs="EPSG:4326")
    if target_crs != "EPSG:4326":
        gdf = gdf.to_crs(target_crs)

    return gdf


def get_county_by_code(code: str) -> Optional[dict]:
    """Look up a single county's geospatial metadata by code."""
    code_normalized = code.zfill(3)
    for c in KENYA_COUNTIES:
        if c["code"] == code_normalized:
            return c
    return None
