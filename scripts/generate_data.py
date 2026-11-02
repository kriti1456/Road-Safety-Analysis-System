"""Deterministic synthetic road crash incident generator.

Generates exactly 10,000 synthetic incident records with realistic temporal,
environmental, and spatial distributions along 18 OpenStreetMap corridors.
The generated dataset is strictly demonstration data and not real-world crashes.
"""

import hashlib
import json
from pathlib import Path
import sys

# Ensure project root is in sys.path when executed directly
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import pandas as pd
from pyproj import Transformer

from backend.domain import (
    ANCHORS_PATH,
    END,
    FACTORS,
    INCIDENTS_PATH,
    MANIFEST_PATH,
    SEED,
    START,
    USERS,
    VEHICLES,
)


def generate(n: int = 10000, seed: int = SEED) -> pd.DataFrame:
    """Generate n synthetic incident records using a deterministic random seed.

    Args:
        n: Number of records to generate (default 10,000).
        seed: Random number generator seed for strict reproducibility.

    Returns:
        DataFrame containing generated incident records.
    """
    anchors = json.loads(ANCHORS_PATH.read_text(encoding="utf-8"))["anchors"]
    rng = np.random.default_rng(seed)

    forward = Transformer.from_crs(4326, 32643, always_xy=True)
    inverse = Transformer.from_crs(32643, 4326, always_xy=True)

    # Base geographical distribution weights across corridor anchors
    corridor_weights = np.linspace(2.2, 0.6, len(anchors))
    corridor_weights /= corridor_weights.sum()

    days = pd.date_range(START, END, freq="D")
    # Upweight monsoon months (July, August, September)
    day_weights = np.array([1.2 if d.month in (7, 8, 9) else 1.0 for d in days])
    day_weights /= day_weights.sum()

    # Hourly distribution with morning and evening traffic peaks
    hourly_distribution = np.array(
        [1, 1, 1, 1, 1, 2, 3, 4, 6, 4, 3, 3, 3, 3, 4, 4, 5, 8, 9, 8, 6, 4, 3, 2],
        dtype=float,
    )
    hourly_distribution /= hourly_distribution.sum()

    rows = []
    for i in range(n):
        day = pd.Timestamp(rng.choice(days))
        w = corridor_weights.copy()
        # Intensify the last two corridors in the final 90 days to simulate emerging activity
        if day >= pd.Timestamp("2026-04-02"):
            w[-2:] *= 4
            w /= w.sum()

        chosen_anchor = anchors[int(rng.choice(len(anchors), p=w))]
        segment = chosen_anchor["segment"]
        t = rng.random()

        # Interpolate along the OSM road segment and add bounded UTM coordinate noise
        x1, y1 = forward.transform(segment[0][0], segment[0][1])
        x2, y2 = forward.transform(segment[1][0], segment[1][1])
        noise_x = rng.uniform(-8, 8)
        noise_y = rng.uniform(-8, 8)
        interp_x = x1 + t * (x2 - x1) + noise_x
        interp_y = y1 + t * (y2 - y1) + noise_y

        lon, lat = inverse.transform(interp_x, interp_y)
        hour = int(rng.choice(24, p=hourly_distribution))
        is_night = (hour < 6) or (hour >= 18)

        # Environmental conditions
        is_monsoon = day.month in (7, 8, 9)
        weather_probs = [0.72, 0.23, 0.05] if is_monsoon else [0.87, 0.07, 0.06]
        weather = str(rng.choice(["Clear", "Rain", "Fog"], p=weather_probs))

        # Severity probability modeled with night and weather adjustments
        p_fatal = 0.035 + (0.025 if is_night else 0.0) + (0.02 if weather == "Rain" else 0.0)
        p_serious = 0.23 + (0.06 if is_night else 0.0)
        p_minor = 1.0 - p_fatal - p_serious
        severity = str(rng.choice(["Fatal", "Serious", "Minor"], p=[p_fatal, p_serious, p_minor]))

        # Vehicle and road user mix
        vehicle = str(rng.choice(VEHICLES, p=[0.42, 0.29, 0.08, 0.06, 0.10, 0.05]))
        if vehicle == "Bicycle":
            road_user = "Cyclist"
        else:
            road_user = str(rng.choice(USERS[:4], p=[0.30, 0.35, 0.18, 0.17]))

        fatalities = int(rng.integers(1, 3)) if severity == "Fatal" else 0
        casualties = max(fatalities, int(rng.integers(1, 4)))

        minute = int(rng.integers(60))
        incident_dt = day + pd.Timedelta(hours=hour, minutes=minute)

        rows.append({
            "incident_id": f"CHD-{i+1:05d}",
            "incident_datetime": incident_dt.isoformat(),
            "latitude": round(lat, 7),
            "longitude": round(lon, 7),
            "area_name": chosen_anchor["name"],
            "road_name": chosen_anchor["road_name"],
            "anchor_id": chosen_anchor["id"],
            "severity": severity,
            "vehicle_type": vehicle,
            "road_user_type": road_user,
            "contributing_factor": str(rng.choice(FACTORS, p=[0.31, 0.20, 0.16, 0.15, 0.10, 0.08])),
            "weather_condition": weather,
            "lighting_condition": "Dark" if is_night else "Daylight",
            "road_surface_condition": "Wet" if weather == "Rain" else "Dry",
            "collision_type": str(rng.choice(["Angle", "Rear-end", "Single vehicle", "Pedestrian impact"])),
            "casualties": casualties,
            "fatalities": fatalities,
            "hour": hour,
            "day_of_week": incident_dt.day_name(),
            "month": incident_dt.month,
            "year": incident_dt.year,
            "simulated_data_flag": True,
        })

    return pd.DataFrame(rows)


def main() -> None:
    """Generate dataset and write CSV along with SHA-256 provenance manifest."""
    df = generate()
    INCIDENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(INCIDENTS_PATH, index=False, lineterminator="\n")

    manifest = {
        "seed": SEED,
        "rows": len(df),
        "start": START,
        "end": END,
        "sha256": hashlib.sha256(INCIDENTS_PATH.read_bytes()).hexdigest(),
        "mode": "synthetic",
        "generator_version": "1.0",
        "assumptions": [
            "Evening peak sampling",
            "Monsoon days upweighted 20%",
            "Fatal probability +2.5 percentage points at night, +2 points in rain",
            "Serious probability +6 points at night",
            "Last two anchors receive 4x geographical selection weight in final 90 days",
            "Uneven corridor weights and vehicle mix are invented",
        ],
    }
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Generated {len(df)} records -> {INCIDENTS_PATH}")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
