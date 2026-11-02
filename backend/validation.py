"""Data validation engine for synthetic road safety incident records.

Audits raw tabular datasets against strict domain schema constraints without
silently discarding corrupted or invalid records. Generates an auditable
quality log while deriving calendar and analytical features.
"""

from typing import Any, Dict, List, Sequence, Tuple
import pandas as pd

from backend.domain import END, FACTORS, START, USERS, VEHICLES, WEIGHTS

# Required columns for incident records
REQUIRED_COLUMNS: List[str] = [
    "incident_id",
    "incident_datetime",
    "latitude",
    "longitude",
    "area_name",
    "road_name",
    "severity",
    "vehicle_type",
    "road_user_type",
    "contributing_factor",
    "weather_condition",
    "lighting_condition",
    "road_surface_condition",
    "collision_type",
    "casualties",
    "fatalities",
    "simulated_data_flag",
]

# Backward compatibility alias
REQUIRED: List[str] = REQUIRED_COLUMNS

# Geographical study extent bounds (Chandigarh urban corridor)
LATITUDE_BOUNDS: Tuple[float, float] = (30.69, 30.77)
LONGITUDE_BOUNDS: Tuple[float, float] = (76.73, 76.83)

# Allowed controlled categories for environmental features
ALLOWED_WEATHER: List[str] = ["Clear", "Rain", "Fog"]
ALLOWED_LIGHTING: List[str] = ["Dark", "Daylight"]
ALLOWED_SURFACE: List[str] = ["Wet", "Dry"]
ALLOWED_COLLISION: List[str] = ["Angle", "Rear-end", "Single vehicle", "Pedestrian impact"]


def validate(
    raw: pd.DataFrame,
    area_names: Sequence[str],
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Validate incident records and derive calendar and analytical features.

    Args:
        raw: Input DataFrame to validate.
        area_names: Collection of permitted corridor/anchor area names.

    Returns:
        A tuple of (clean_df, quality_metadata_dict).
    """
    df = raw.copy()
    issues: List[Dict[str, Any]] = []
    bad_mask = pd.Series(False, index=df.index)

    # 1. Check for required schema columns
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        return df.iloc[:0], {
            "valid": 0,
            "invalid": len(df),
            "missing_columns": missing_cols,
            "missing_values": {},
            "issues": [
                {"row": None, "field": col, "reason": "missing column"}
                for col in missing_cols
            ],
        }

    # 2. Missing value audit across required fields
    missing_counts = {col: int(df[col].isna().sum()) for col in REQUIRED_COLUMNS}

    def flag_issue(mask: pd.Series, field: str, reason: str) -> None:
        """Mark invalid rows and record each offending row in the issue registry."""
        nonlocal bad_mask
        resolved_mask = mask.fillna(True)
        bad_mask |= resolved_mask
        for idx in df.index[resolved_mask]:
            issues.append({"row": int(idx), "field": field, "reason": reason})

    for col in REQUIRED_COLUMNS:
        flag_issue(df[col].isna(), col, "missing value")

    # 3. Duplicate incident identifiers
    flag_issue(
        df["incident_id"].duplicated(keep=False),
        "incident_id",
        "duplicate ID",
    )

    # 4. Datetime parsing and temporal extent check
    df["dt"] = pd.to_datetime(df["incident_datetime"], errors="coerce", utc=True).dt.tz_convert(None)
    flag_issue(df["dt"].isna(), "incident_datetime", "invalid datetime")

    start_timestamp = pd.Timestamp(START)
    end_timestamp = pd.Timestamp(END) + pd.Timedelta(days=1)
    flag_issue(
        (df["dt"] < start_timestamp) | (df["dt"] >= end_timestamp),
        "incident_datetime",
        "outside documented dataset period",
    )

    # 5. Geographic bounding box validation
    for num_col in ["latitude", "longitude", "casualties", "fatalities"]:
        df[num_col] = pd.to_numeric(df[num_col], errors="coerce")

    flag_issue(
        ~df["latitude"].between(LATITUDE_BOUNDS[0], LATITUDE_BOUNDS[1]),
        "latitude",
        "outside documented study extent",
    )
    flag_issue(
        ~df["longitude"].between(LONGITUDE_BOUNDS[0], LONGITUDE_BOUNDS[1]),
        "longitude",
        "outside documented study extent",
    )

    # 6. Categorical domain checks
    controlled_categories = {
        "severity": list(WEIGHTS.keys()),
        "vehicle_type": VEHICLES,
        "road_user_type": USERS,
        "contributing_factor": FACTORS,
        "area_name": list(area_names),
        "weather_condition": ALLOWED_WEATHER,
        "lighting_condition": ALLOWED_LIGHTING,
        "road_surface_condition": ALLOWED_SURFACE,
        "collision_type": ALLOWED_COLLISION,
    }

    for col_name, allowed_values in controlled_categories.items():
        flag_issue(~df[col_name].isin(allowed_values), col_name, "unknown category")

    # 7. Casualty and fatality logical consistency
    invalid_counts = (
        (df["casualties"] < 1)
        | (df["fatalities"] < 0)
        | (df["fatalities"] > df["casualties"])
        | (df["casualties"] % 1 != 0)
        | (df["fatalities"] % 1 != 0)
    )
    flag_issue(invalid_counts, "casualties", "invalid counts")

    inconsistent_fatalities = (
        (df["severity"] == "Fatal") & (df["fatalities"] < 1)
    ) | (
        (df["severity"] != "Fatal") & (df["fatalities"] != 0)
    )
    flag_issue(inconsistent_fatalities, "fatalities", "inconsistent with severity")

    # 8. Synthetic demonstration flag enforcement
    flag_issue(
        ~df["simulated_data_flag"].isin([True, "True", "true"]),
        "simulated_data_flag",
        "must be synthetic",
    )

    # 9. Clean dataset extraction and feature derivation
    clean = df[~bad_mask].copy()
    clean["hour"] = clean["dt"].dt.hour
    clean["day_of_week"] = clean["dt"].dt.day_name()
    clean["month"] = clean["dt"].dt.month
    clean["year"] = clean["dt"].dt.year
    clean["weight"] = clean["severity"].map(WEIGHTS).astype(int)
    clean["night"] = (clean["hour"] < 6) | (clean["hour"] >= 18)

    quality_summary = {
        "valid": len(clean),
        "invalid": int(bad_mask.sum()),
        "missing_columns": [],
        "missing_values": missing_counts,
        "duplicate_ids": int(df["incident_id"].duplicated(keep=False).sum()),
        "issues": issues,
        "derived_features": (
            "hour, day_of_week, month, year recalculated from datetime; "
            "weight and night derived"
        ),
    }

    return clean, quality_summary
