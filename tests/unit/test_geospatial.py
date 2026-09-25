"""Unit tests for geospatial boundaries and Kenya county mappings."""

from agririsk.geospatial.boundaries import get_counties_geodataframe, get_county_by_code


def test_geodataframe_creation():
    """Verify GeoPandas GeoDataFrame contains 47 valid county geometries."""
    gdf = get_counties_geodataframe()
    assert len(gdf) == 47
    assert gdf.crs.to_string() == "EPSG:4326"
    assert "county_code" in gdf.columns
    assert "asal_category" in gdf.columns

    # Check bounds (Kenya roughly: lat -5 to 5.5, lon 33.5 to 42.5)
    for geom in gdf.geometry:
        assert 33.5 <= geom.x <= 42.5
        assert -5.0 <= geom.y <= 5.5


def test_county_lookup_by_code():
    """Verify looking up single county by code."""
    c = get_county_by_code("023")
    assert c is not None
    assert c["name"] == "Turkana"
    assert c["asal_category"] == "Arid"

    # Single digit padding
    c1 = get_county_by_code("1")
    assert c1 is not None
    assert c1["name"] == "Mombasa"
