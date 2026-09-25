"""Generate polygon boundary GeoJSON for Kenya's 47 counties based on spatial partitioning.

Outputs:
    data/geospatial/kenya_counties.geojson
"""

import json
from pathlib import Path
import numpy as np
from scipy.spatial import Voronoi
from shapely.geometry import Polygon, box, mapping
import geopandas as gpd
from agririsk.core.constants import KENYA_COUNTIES

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def generate_kenya_county_geojson():
    output_dir = PROJECT_ROOT / "data" / "geospatial"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "kenya_counties.geojson"

    # Kenya geographical bounding envelope (approximate national border box with buffer)
    kenya_bbox = box(33.8, -4.8, 41.95, 5.45)

    points = np.array([[c["lon"], c["lat"]] for c in KENYA_COUNTIES])
    n_points = len(points)

    # To bound Voronoi diagram cleanly, add boundary buffer points far outside
    buffer_points = np.array([
        [28.0, -10.0], [28.0, 10.0], [48.0, -10.0], [48.0, 10.0],
        [38.0, -12.0], [38.0, 12.0], [25.0, 0.0], [50.0, 0.0]
    ])
    all_points = np.vstack([points, buffer_points])

    vor = Voronoi(all_points)

    features = []

    for i in range(n_points):
        county = KENYA_COUNTIES[i]
        region_idx = vor.point_region[i]
        region = vor.regions[region_idx]

        if not region or -1 in region:
            continue

        poly_coords = [vor.vertices[v] for v in region]
        raw_poly = Polygon(poly_coords)

        # Clip polygon to Kenya bounding envelope
        clipped_poly = raw_poly.intersection(kenya_bbox)

        if clipped_poly.is_empty:
            continue

        features.append({
            "type": "Feature",
            "id": county["code"],
            "properties": {
                "county_code": county["code"],
                "county_name": county["name"],
                "asal_category": county["asal_category"],
                "latitude": county["lat"],
                "longitude": county["lon"],
            },
            "geometry": mapping(clipped_poly)
        })

    geojson_data = {
        "type": "FeatureCollection",
        "crs": {
            "type": "name",
            "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}
        },
        "features": features
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(geojson_data, f, indent=2)

    print(f"Generated {output_file} with {len(features)} county polygon boundaries.")
    return output_file


if __name__ == "__main__":
    generate_kenya_county_geojson()
