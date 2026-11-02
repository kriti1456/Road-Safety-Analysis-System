"""Domain models, configuration paths, and analytical constants.

Contains all shared domain parameters, geographical extent boundaries,
severity weights, vehicle/factor/user taxonomies, and hypothetical
counterfactual intervention specifications.

NOTE: All crash records in this project are synthetic demonstration records.
Weights and parameters are illustrative analytical models, not official standards.
"""

from pathlib import Path
from typing import Any, Dict, List

# ---------------------------------------------------------------------------
# Project Directories & File Paths
# ---------------------------------------------------------------------------
ROOT_DIR: Path = Path(__file__).resolve().parents[1]
DATA_DIR: Path = ROOT_DIR / "data"
RAW_DATA_DIR: Path = DATA_DIR / "raw"
PROCESSED_DATA_DIR: Path = DATA_DIR / "processed"
SYNTHETIC_DATA_DIR: Path = DATA_DIR / "synthetic"
STATIC_DIR: Path = ROOT_DIR / "static"
OUTPUTS_DIR: Path = ROOT_DIR / "outputs"

# Specific Dataset File Paths (with fallback to root data dir if needed)
INCIDENTS_PATH: Path = (
    SYNTHETIC_DATA_DIR / "incidents.csv"
    if (SYNTHETIC_DATA_DIR / "incidents.csv").exists()
    else DATA_DIR / "incidents.csv"
)

MANIFEST_PATH: Path = (
    SYNTHETIC_DATA_DIR / "manifest.json"
    if (SYNTHETIC_DATA_DIR / "manifest.json").exists()
    else DATA_DIR / "manifest.json"
)

ANCHORS_PATH: Path = (
    PROCESSED_DATA_DIR / "anchors.json"
    if (PROCESSED_DATA_DIR / "anchors.json").exists()
    else DATA_DIR / "anchors.json"
)

GEOGRAPHY_PROVENANCE_PATH: Path = (
    PROCESSED_DATA_DIR / "geography-provenance.json"
    if (PROCESSED_DATA_DIR / "geography-provenance.json").exists()
    else DATA_DIR / "geography-provenance.json"
)

OSM_ROAD_SOURCE_PATH: Path = (
    RAW_DATA_DIR / "osm-road-source.json"
    if (RAW_DATA_DIR / "osm-road-source.json").exists()
    else DATA_DIR / "osm-road-source.json"
)

ROADS_GEOJSON_PATH: Path = STATIC_DIR / "roads.geojson"

# Backward compatibility aliases
ROOT: Path = ROOT_DIR
DATA: Path = DATA_DIR

# ---------------------------------------------------------------------------
# Simulation Parameters & Metadata
# ---------------------------------------------------------------------------
SEED: int = 20261022
START: str = "2024-07-01"
END: str = "2026-06-30"
NOTICE: str = "SYNTHETIC DEMONSTRATION DATA — NOT VERIFIED REAL-WORLD CRASH RECORDS"

# Severity weights: Fatal=3, Serious=2, Minor=1
WEIGHTS: Dict[str, int] = {
    "Fatal": 3,
    "Serious": 2,
    "Minor": 1,
}

# Controlled Categorical Taxonomies
VEHICLES: List[str] = [
    "Two-wheeler",
    "Car",
    "Bicycle",
    "Bus",
    "Goods vehicle",
    "Auto-rickshaw",
]

FACTORS: List[str] = [
    "Speeding",
    "Signal violation",
    "Distraction",
    "Crossing conflict",
    "Poor visibility",
    "Road condition",
]

USERS: List[str] = [
    "Driver",
    "Rider",
    "Pedestrian",
    "Passenger",
    "Cyclist",
]

# ---------------------------------------------------------------------------
# Hypothetical Interventions
# ---------------------------------------------------------------------------
INTERVENTIONS: Dict[str, Dict[str, Any]] = {
    "Speed management": {
        "factor": ["Speeding"],
        "cost": 1800000,
        "reason": "Applies to records assigned the synthetic Speeding factor.",
    },
    "Traffic enforcement": {
        "factor": ["Speeding", "Signal violation", "Distraction"],
        "cost": 900000,
        "reason": "Applies to synthetic speed, signal and distraction factors.",
    },
    "Road lighting": {
        "night": True,
        "cost": 1400000,
        "reason": "Applies to records with dark lighting conditions.",
    },
    "Junction redesign": {
        "factor": ["Signal violation", "Crossing conflict"],
        "cost": 6000000,
        "reason": "Applies to synthetic signal and crossing conflicts.",
    },
    "Pedestrian safety": {
        "user": "Pedestrian",
        "cost": 2200000,
        "reason": "Applies to records involving a pedestrian road user.",
    },
    "Signage and markings": {
        "factor": ["Road condition", "Poor visibility"],
        "cost": 600000,
        "reason": "Applies to synthetic road condition and visibility factors.",
    },
}
