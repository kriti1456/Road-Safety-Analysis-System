"""Optional online refresh script for OpenStreetMap road geometry.

NOTE: This script is only needed for refreshing the underlying OSM snapshot
from live OSM API endpoints. The application already includes a complete
local snapshot in data/raw/osm-road-source.json and does not require internet access.

Respects OpenStreetMap API rate limits and terms of service.
"""

import json
from pathlib import Path
import sys
import urllib.request
import xml.etree.ElementTree as ET

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.domain import OSM_ROAD_SOURCE_PATH, RAW_DATA_DIR


def fetch_osm_tiles() -> None:
    """Fetch 9 bounding-box XML tiles from OSM API v0.6 and build a merged JSON extract."""
    work_dir = PROJECT_ROOT / "work" / "osm-tiles"
    work_dir.mkdir(parents=True, exist_ok=True)

    headers = {
        "User-Agent": "ChandigarhRoadSafetyIntelligence/1.0 (academic research demonstrator)",
    }

    nodes = {}
    ways = {}

    for i in range(3):
        for j in range(3):
            left = 76.75 + i * 0.02
            bottom = 30.70 + j * 0.02
            right = left + 0.02
            top = bottom + 0.02
            url = f"https://api.openstreetmap.org/api/0.6/map?bbox={left:.3f},{bottom:.3f},{right:.3f},{top:.3f}"
            tile_path = work_dir / f"{i}-{j}.xml"

            print(f"Fetching tile ({i}, {j}) from {url}...")
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=60) as resp:
                tile_path.write_bytes(resp.read())

            root = ET.parse(tile_path).getroot()
            for node in root.findall("node"):
                nodes[node.attrib["id"]] = {
                    "lat": float(node.attrib["lat"]),
                    "lon": float(node.attrib["lon"]),
                }

            for way in root.findall("way"):
                tags = {t.attrib["k"]: t.attrib["v"] for t in way.findall("tag")}
                highway_type = tags.get("highway")
                if highway_type in ["primary", "secondary", "trunk", "tertiary"] and tags.get("name"):
                    ways[way.attrib["id"]] = {
                        "type": "way",
                        "id": int(way.attrib["id"]),
                        "tags": tags,
                        "node_ids": [nd.attrib["ref"] for nd in way.findall("nd")],
                    }

    # Reconstruct way geometries from referenced node coordinates
    result = []
    for way in sorted(ways.values(), key=lambda w: w["id"]):
        if all(nid in nodes for nid in way["node_ids"]):
            way["geometry"] = [nodes[nid] for nid in way.pop("node_ids")]
            result.append(way)

    OSM_ROAD_SOURCE_PATH.parent.mkdir(parents=True, exist_ok=True)
    OSM_ROAD_SOURCE_PATH.write_text(
        json.dumps({"elements": result}, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    print(
        f"Cached {len(result)} complete named ways to {OSM_ROAD_SOURCE_PATH}. "
        "Run scripts/prepare_geography.py next to update anchors and GeoJSON."
    )


if __name__ == "__main__":
    fetch_osm_tiles()
