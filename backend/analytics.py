"""Deterministic server-side descriptive analytics in fixed UTM 43N metre cells.

Computes spatial aggregations, fixed-metric grid hotspot classifications,
90-day emerging activity tracking, and counterfactual intervention simulations.
All spatial projections use EPSG:32643 (UTM Zone 43N).
"""

import json
from typing import Any, Dict, List, Optional, Sequence, Tuple
import numpy as np
import pandas as pd
from pyproj import Transformer

from backend.domain import ANCHORS_PATH, INCIDENTS_PATH, INTERVENTIONS, WEIGHTS
from backend.validation import validate

# Coordinate reference system transformers
# WGS84 (EPSG:4326) <-> UTM Zone 43N (EPSG:32643)
FORWARD: Transformer = Transformer.from_crs(4326, 32643, always_xy=True)
INVERSE: Transformer = Transformer.from_crs(32643, 4326, always_xy=True)

# Grid cell resolution in metres (500m x 500m)
CELL: int = 500


def load() -> Tuple[pd.DataFrame, Dict[str, Any], List[Dict[str, Any]], float, float]:
    """Load, validate, and index the incident dataset and corridor anchors.

    Returns:
        Tuple of (clean_df, quality_report, anchors_list, q75_threshold, q90_threshold).
    """
    anchors_data = json.loads(ANCHORS_PATH.read_text(encoding="utf-8"))
    anchors = anchors_data["anchors"]
    allowed_area_names = [anchor["name"] for anchor in anchors]

    raw_df = pd.read_csv(INCIDENTS_PATH)
    clean_df, quality = validate(raw_df, allowed_area_names)

    if clean_df.empty:
        raise RuntimeError("No valid records: inspect dataset validation issues")

    # Project longitude/latitude into metric UTM easting/northing
    easting, northing = FORWARD.transform(
        clean_df["longitude"].to_numpy(),
        clean_df["latitude"].to_numpy(),
    )
    clean_df["gx"] = np.floor(easting / CELL).astype(int)
    clean_df["gy"] = np.floor(northing / CELL).astype(int)
    clean_df["cell_id"] = clean_df["gx"].astype(str) + "_" + clean_df["gy"].astype(str)

    # Compute baseline 75th and 90th percentile burden thresholds across all occupied cells
    cell_scores = clean_df.groupby("cell_id")["weight"].sum()
    q75_threshold = float(cell_scores.quantile(0.75))
    q90_threshold = float(cell_scores.quantile(0.90))

    return clean_df, quality, anchors, q75_threshold, q90_threshold


# Global analytical dataset loaded into memory on server initialization
DF, QUALITY, ANCHORS, Q75, Q90 = load()


def filtered(filters: Any) -> pd.DataFrame:
    """Filter the incident dataset according to active query parameters.

    Args:
        filters: Filter parameters object specifying date range, categories, and cell scope.

    Returns:
        Filtered DataFrame of incident records.
    """
    start_ts = pd.Timestamp(filters.start)
    end_ts = pd.Timestamp(filters.end) + pd.Timedelta(days=1)

    subset = DF[(DF["dt"] >= start_ts) & (DF["dt"] < end_ts)]

    criteria = [
        ("area", "area_name"),
        ("severity", "severity"),
        ("vehicle", "vehicle_type"),
        ("factor", "contributing_factor"),
        ("cell", "cell_id"),
    ]

    for filter_attr, df_col in criteria:
        val = getattr(filters, filter_attr, None)
        if val:
            subset = subset[subset[df_col] == val]

    if filters.period == "Night":
        subset = subset[subset["night"]]
    elif filters.period == "Day":
        subset = subset[~subset["night"]]

    return subset


def distribution(
    data: pd.DataFrame,
    column: str,
    labels: Optional[Sequence[Any]] = None,
) -> List[Dict[str, Any]]:
    """Compute frequency counts for a column against expected categorical labels."""
    counts = data[column].value_counts()
    keys = labels if labels is not None else counts.index.tolist()
    return [{"label": str(k), "count": int(counts.get(k, 0))} for k in keys]


def basic(data: pd.DataFrame) -> Dict[str, Any]:
    """Calculate summary statistics and weighted burden for an incident subset.

    Weighted burden = 3 * Fatal + 2 * Serious + 1 * Minor.
    """
    severity_counts = {
        sev: int((data["severity"] == sev).sum())
        for sev in WEIGHTS
    }
    total_count = len(data)
    weighted_score = int(data["weight"].sum())
    fatalities = int(data["fatalities"].sum())
    casualties = int(data["casualties"].sum())

    severe_count = severity_counts["Fatal"] + severity_counts["Serious"]
    severe_share = round(100.0 * severe_count / total_count, 2) if total_count else 0.0

    return {
        "count": total_count,
        "weighted_score": weighted_score,
        "severity": severity_counts,
        "fatalities": fatalities,
        "casualties": casualties,
        "severe_share": severe_share,
    }


def classification(score: float | int, count: int) -> str:
    """Classify a grid cell using full-dataset frozen percentile thresholds."""
    if count < 10:
        return "Sparse"
    if score >= Q90:
        return "High"
    if score >= Q75:
        return "Elevated"
    return "Lower"


def grid(data: pd.DataFrame) -> List[Dict[str, Any]]:
    """Aggregate incidents into fixed 500m x 500m spatial cells with polygon boundaries."""
    cells: List[Dict[str, Any]] = []

    for cell_key, group in data.groupby("cell_id", sort=True):
        gx = int(group["gx"].iloc[0])
        gy = int(group["gy"].iloc[0])

        # Convert 500m metric cell corners back to WGS84 (lon, lat)
        corners = [
            INVERSE.transform(gx * CELL, gy * CELL),
            INVERSE.transform((gx + 1) * CELL, gy * CELL),
            INVERSE.transform((gx + 1) * CELL, (gy + 1) * CELL),
            INVERSE.transform(gx * CELL, (gy + 1) * CELL),
        ]
        center_lon, center_lat = INVERSE.transform((gx + 0.5) * CELL, (gy + 0.5) * CELL)

        base_metrics = basic(group)
        cell_record = {
            "id": cell_key,
            "area": group["area_name"].mode().iloc[0],
            "latitude": center_lat,
            "longitude": center_lon,
            "polygon": [[lat, lon] for lon, lat in corners],
            **base_metrics,
            "classification": classification(
                base_metrics["weighted_score"],
                base_metrics["count"],
            ),
        }
        cells.append(cell_record)

    # Sort descending by weighted score, then count, then cell identifier
    cells.sort(key=lambda r: (-r["weighted_score"], -r["count"], r["id"]))
    return cells


def emerging(data: pd.DataFrame, filters: Any) -> Dict[str, Any]:
    """Detect emerging hotspots by comparing two equal 90-day observation windows.

    Guardrail rules:
      - Requires baseline >= 5
      - Requires recent >= 10
      - Requires absolute increase >= 5
      - Requires ratio (recent/baseline) >= 1.5
    """
    end_date = pd.Timestamp(filters.end) + pd.Timedelta(days=1)
    cutoff_date = end_date - pd.Timedelta(days=90)
    baseline_date = cutoff_date - pd.Timedelta(days=90)

    is_available = pd.Timestamp(filters.start) <= baseline_date
    window_meta = {
        "available": is_available,
        "baseline_start": baseline_date.date().isoformat(),
        "baseline_end": (cutoff_date - pd.Timedelta(days=1)).date().isoformat(),
        "recent_start": cutoff_date.date().isoformat(),
        "recent_end": filters.end,
        "window_days": 90,
        "rule": (
            "baseline >= 5, recent >= 10, absolute increase >= 5 and ratio >= 1.5; "
            "exploratory flag, not a significance test"
        ),
    }

    if not is_available:
        return {
            "windows": window_meta,
            "cells": [],
            "reason": "Select at least 180 days for two complete 90-day windows.",
        }

    base_counts = (
        data[(data["dt"] >= baseline_date) & (data["dt"] < cutoff_date)]
        .groupby("cell_id")
        .size()
    )
    recent_counts = (
        data[(data["dt"] >= cutoff_date) & (data["dt"] < end_date)]
        .groupby("cell_id")
        .size()
    )

    emerging_cells: List[Dict[str, Any]] = []
    for cell in grid(data):
        b_count = int(base_counts.get(cell["id"], 0))
        r_count = int(recent_counts.get(cell["id"], 0))
        delta = r_count - b_count
        ratio = (r_count / b_count) if b_count > 0 else None
        qualifies = (b_count >= 5) and (r_count >= 10) and (delta >= 5) and (ratio is not None and ratio >= 1.5)

        if qualifies:
            status_label = "Emerging"
        elif b_count < 5:
            status_label = "Sparse baseline"
        else:
            status_label = "Established / stable"

        emerging_cells.append(
            {
                **cell,
                "baseline": b_count,
                "recent": r_count,
                "delta": delta,
                "ratio": round(ratio, 3) if ratio is not None else None,
                "emerging": bool(qualifies),
                "status": status_label,
            }
        )

    emerging_cells.sort(key=lambda c: (not c["emerging"], -c["delta"], c["id"]))
    return {"windows": window_meta, "cells": emerging_cells}


def aggregate(data: pd.DataFrame, filters: Any) -> Dict[str, Any]:
    """Compute complete analytical aggregations for the filtered dataset."""
    start_month = pd.Timestamp(filters.start).replace(day=1)
    end_month = pd.Timestamp(filters.end).replace(day=1)
    month_range = pd.date_range(start_month, end_month, freq="MS")

    monthly_series = data.assign(ym=data["dt"].dt.strftime("%Y-%m")).groupby("ym").size()
    monthly_counts = [
        {"label": dt.strftime("%Y-%m"), "count": int(monthly_series.get(dt.strftime("%Y-%m"), 0))}
        for dt in month_range
    ]

    area_summaries: List[Dict[str, Any]] = []
    for area_name, group in data.groupby("area_name"):
        area_grid = grid(group)
        hotspot_count = sum(c["classification"] == "High" for c in area_grid)
        area_summaries.append(
            {
                "area": area_name,
                **basic(group),
                "peak_hour": int(group["hour"].mode().iloc[0]),
                "dominant_factor": group["contributing_factor"].mode().iloc[0],
                "hotspot_cells": hotspot_count,
            }
        )

    area_summaries.sort(key=lambda a: (-a["weighted_score"], a["area"]))
    total_incidents = len(data)
    cumulative_count = 0
    for area in area_summaries:
        cumulative_count += area["count"]
        area["cumulative_share"] = (
            round(cumulative_count / total_incidents * 100.0, 2)
            if total_incidents
            else 0.0
        )

    grid_cells = grid(data)
    emerging_info = emerging(data, filters)

    # Window period comparison (dividing selection into two equal halves)
    total_selected_days = (pd.Timestamp(filters.end) - pd.Timestamp(filters.start)).days + 1
    half_days = total_selected_days // 2

    if half_days > 0:
        current_period = data[data["dt"] >= pd.Timestamp(filters.end) + pd.Timedelta(days=1 - half_days)]
        prev_start = pd.Timestamp(filters.end) + pd.Timedelta(days=1 - 2 * half_days)
        prev_end = pd.Timestamp(filters.end) + pd.Timedelta(days=1 - half_days)
        previous_period = data[(data["dt"] >= prev_start) & (data["dt"] < prev_end)]
    else:
        current_period = data.iloc[:0]
        previous_period = data.iloc[:0]

    prev_count = len(previous_period)
    curr_count = len(current_period)
    delta_count = curr_count - prev_count
    pct_change = round(delta_count / prev_count * 100.0, 1) if prev_count else None

    # Crosstab matrices
    sev_time_matrix = (
        pd.crosstab(data["hour"], data["severity"])
        .reindex(index=range(24), columns=list(WEIGHTS.keys()), fill_value=0)
        .to_dict(orient="index")
    )
    sev_veh_matrix = (
        pd.crosstab(data["vehicle_type"], data["severity"])
        .reindex(columns=list(WEIGHTS.keys()), fill_value=0)
        .to_dict(orient="index")
    )

    weekday_order = [
        "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"
    ]

    return {
        "metrics": {
            **basic(data),
            "hotspots": sum(c["classification"] == "High" for c in grid_cells),
            "occupied_cells": len(grid_cells),
            "top_area": area_summaries[0]["area"] if area_summaries else None,
            "emerging_count": sum(c["emerging"] for c in emerging_info["cells"]),
        },
        "comparison": {
            "window_days": half_days,
            "previous": prev_count,
            "current": curr_count,
            "delta": delta_count,
            "percent": pct_change,
        },
        "monthly": monthly_counts,
        "annual": distribution(data, "year", sorted(data["year"].unique().tolist())),
        "hours": distribution(data, "hour", range(24)),
        "weekdays": distribution(data, "day_of_week", weekday_order),
        "severities": distribution(data, "severity", list(WEIGHTS.keys())),
        "vehicles": distribution(data, "vehicle_type"),
        "factors": distribution(data, "contributing_factor"),
        "users": distribution(data, "road_user_type"),
        "weather": distribution(data, "weather_condition"),
        "seasons": distribution(data, "month", range(1, 13)),
        "areas": area_summaries,
        "grid": grid_cells,
        "emerging": emerging_info,
        "severity_time": sev_time_matrix,
        "severity_vehicle": sev_veh_matrix,
    }


def records(data: pd.DataFrame) -> List[Dict[str, Any]]:
    """Convert incident DataFrame to dictionary records excluding internal columns."""
    columns_to_drop = ["dt", "weight", "night", "gx", "gy"]
    return data.drop(columns=columns_to_drop, errors="ignore").to_dict(orient="records")


def eligible(data: pd.DataFrame, kind: str) -> pd.Series:
    """Return boolean mask of records matching an intervention's eligibility criteria."""
    spec = INTERVENTIONS[kind]
    if "night" in spec:
        return data["night"]
    if "user" in spec:
        return data["road_user_type"] == spec["user"]
    return data["contributing_factor"].isin(spec["factor"])


def simulate(
    data: pd.DataFrame,
    filters: Any,
    kind: str,
    intensity: float,
    months: int,
    effectiveness: float,
    uncertainty: float,
) -> Dict[str, Any]:
    """Simulate hypothetical counterfactual impact of an intervention.

    Formula:
      reduction = eligible_baseline * intensity * effectiveness
      ineligible records remain unchanged.
    """
    days = (pd.Timestamp(filters.end) - pd.Timestamp(filters.start)).days + 1
    scale = months * 365.25 / 12 / days
    target = data[eligible(data, kind)]

    baseline_count = len(data) * scale
    baseline_score = float(data["weight"].sum()) * scale
    reduction_rate = intensity * effectiveness

    incident_reduction = len(target) * scale * reduction_rate
    weighted_reduction = float(target["weight"].sum()) * scale * reduction_rate

    low_eff = max(0.0, effectiveness - uncertainty)
    high_eff = min(1.0, effectiveness + uncertainty)

    projected_count = baseline_count - incident_reduction
    projected_weight = baseline_score - weighted_reduction

    min_projected = baseline_count - len(target) * scale * intensity * high_eff
    max_projected = baseline_count - len(target) * scale * intensity * low_eff

    illustrative_cost = round(INTERVENTIONS[kind]["cost"] * intensity * months / 12)

    return {
        "intervention": kind,
        "mode": "hypothetical",
        "assumptions": {
            "intensity": intensity,
            "months": months,
            "effectiveness": effectiveness,
            "uncertainty": uncertainty,
            "observed_days": days,
            "scaling": "duration months * 365.25 / 12 / selected days",
            "formula": "eligible baseline * intensity * effectiveness; unchanged ineligible records",
            "eligibility": INTERVENTIONS[kind]["reason"],
        },
        "observed_count": len(data),
        "eligible_count": len(target),
        "baseline": round(baseline_count, 3),
        "projected": round(projected_count, 3),
        "reduction": round(incident_reduction, 3),
        "baseline_weight": round(baseline_score, 3),
        "projected_weight": round(projected_weight, 3),
        "range": [round(min_projected, 3), round(max_projected, 3)],
        "illustrative_cost_inr": illustrative_cost,
        "limitation": (
            "Fractional expected counts, not historical incidents. "
            "Assumption sensitivity band, not a confidence interval. "
            "Costs and effectiveness are invented; no causal inference or validated forecast."
        ),
    }
