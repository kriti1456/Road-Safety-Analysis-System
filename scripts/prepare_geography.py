"""Build OpenStreetMap road extract, GeoJSON geometry, and 18 corridor anchors.

Extracts named primary, secondary, trunk, and tertiary ways from the raw OSM snapshot,
computes 18 geographically distributed road anchors for spatial clustering,
and outputs static/roads.geojson and data/processed/anchors.json.
"""

import json
import math
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.domain import (
    ANCHORS_PATH,
    GEOGRAPHY_PROVENANCE_PATH,
    OSM_ROAD_SOURCE_PATH,
    ROADS_GEOJSON_PATH,
)


def prepare_geography() -> None:
    """Process raw OSM elements into GeoJSON network and 18 anchor corridors."""
    raw_content = json.loads(OSM_ROAD_SOURCE_PATH.read_text(encoding="utf-8"))
    ways = [
        element for element in raw_content["elements"]
        if element.get("geometry") and element.get("tags", {}).get("name")
    ]

    features = []
    candidates = []

    for way in sorted(ways, key=lambda w: w["id"]):
        coords = [[pt["lon"], pt["lat"]] for pt in way["geometry"]]
        features.append({
            "type": "Feature",
            "properties": {
                "name": way["tags"]["name"],
                "osm_way_id": way["id"],
                "highway": way["tags"]["highway"],
            },
            "geometry": {
                "type": "LineString",
                "coordinates": coords,
            },
        })

        for pt_a, pt_b in zip(coords, coords[1:]):
            mid_lon = (pt_a[0] + pt_b[0]) / 2.0
            mid_lat = (pt_a[1] + pt_b[1]) / 2.0
            approx_dist = math.hypot(
                (pt_a[0] - pt_b[0]) * 95500.0,
                (pt_a[1] - pt_b[1]) * 111000.0,
            )
            # Filter candidate segments within Chandigarh urban bounds and reasonable lengths
            if (
                30.695 < mid_lat < 30.765
                and 76.735 < mid_lon < 76.825
                and 40 < approx_dist < 450
            ):
                candidates.append({
                    "road_name": way["tags"]["name"],
                    "osm_way_id": way["id"],
                    "segment": [pt_a, pt_b],
                    "longitude": mid_lon,
                    "latitude": mid_lat,
                })

    # Select 18 well-spaced corridor anchor segments (minimum 850m separation)
    selected_anchors = []
    for candidate in sorted(candidates, key=lambda c: (c["osm_way_id"], c["latitude"])):
        is_separated = all(
            math.hypot(
                (candidate["longitude"] - other["longitude"]) * 95500.0,
                (candidate["latitude"] - other["latitude"]) * 111000.0,
            ) > 850.0
            for other in selected_anchors
        )
        if is_separated:
            selected_anchors.append(candidate)
        if len(selected_anchors) == 18:
            break

    for idx, anchor in enumerate(selected_anchors):
        anchor_id = f"A{idx + 1:02d}"
        anchor["id"] = anchor_id
        anchor["name"] = f"{anchor['road_name']} / {anchor_id}"

    provenance = {
        "source": "OpenStreetMap contributors via OSM v0.6 API",
        "endpoint": "https://api.openstreetmap.org/api/0.6/map",
        "query": (
            "Nine map bbox requests, 0.02-degree tiles over longitude 76.75-76.81 "
            "and latitude 30.70-30.76; retain complete named primary, secondary, "
            "trunk and tertiary ways"
        ),
        "retrieved": "2026-10-22",
        "osm_base_timestamp": raw_content.get("osm3s", {}).get("timestamp_osm_base"),
        "license": "ODbL 1.0",
        "attribution": "© OpenStreetMap contributors",
        "source_url": "https://www.openstreetmap.org/copyright",
        "extent": [76.73, 30.69, 76.83, 30.77],
        "notes": (
            "Selected named road segments only. Study extent is not an official city boundary. "
            "Anchor areas are analytical labels, not administrative units."
        ),
    }

    ANCHORS_PATH.parent.mkdir(parents=True, exist_ok=True)
    ANCHORS_PATH.write_text(
        json.dumps({**provenance, "anchors": selected_anchors}, indent=2) + "\n",
        encoding="utf-8",
    )

    ROADS_GEOJSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    ROADS_GEOJSON_PATH.write_text(
        json.dumps(
            {
                "type": "FeatureCollection",
                "attribution": "© OpenStreetMap contributors, ODbL 1.0",
                "features": features,
            },
            separators=(",", ":"),
        ),
        encoding="utf-8",
    )

    GEOGRAPHY_PROVENANCE_PATH.parent.mkdir(parents=True, exist_ok=True)
    GEOGRAPHY_PROVENANCE_PATH.write_text(
        json.dumps(provenance, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"Prepared {len(features)} road features and {len(selected_anchors)} anchor corridors.")
    print(f"Anchors saved to: {ANCHORS_PATH}")
    print(f"GeoJSON saved to: {ROADS_GEOJSON_PATH}")


if __name__ == "__main__":
    prepare_geography()
