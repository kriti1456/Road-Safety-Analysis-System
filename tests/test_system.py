"""Automated backend and analytical contract tests for Chandigarh Road Safety Intelligence.

Validates:
  - Exact 10,000-row deterministic generation and SHA-256 hash match.
  - Data validation rules, column constraints, and issue retention.
  - Fixed 500m UTM metric grid stability and invariance.
  - Metric aggregations, cumulative shares, and cross-tabulations.
  - Multi-criteria filter combinations and date inclusivity.
  - 90-day emerging hotspot detection guardrails.
  - Hypothetical intervention simulation determinism and bounds.
  - API endpoint query/payload validation (HTTP 422).
  - Security headers, CSP, GZip compression, and same-origin static serving.
  - State-sensitive CSV and PDF report generation.
"""

import hashlib
import io
import json

from fastapi.testclient import TestClient
import numpy as np
import pandas as pd
import pytest

from backend.analytics import (
    DF,
    FORWARD,
    QUALITY,
    aggregate,
    emerging,
    filtered,
    grid,
    simulate,
)
from backend.domain import (
    INCIDENTS_PATH,
    INTERVENTIONS,
    MANIFEST_PATH,
)
from backend.main import Filters, app
from backend.validation import validate
from scripts.generate_data import generate

client = TestClient(app)


def test_generation_reproducible():
    """Verify that deterministic generation produces byte-for-byte identical dataset."""
    expected = INCIDENTS_PATH.read_bytes()
    regenerated = generate().to_csv(index=False, lineterminator="\n").encode("utf-8")
    assert expected == regenerated

    expected_hash = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))["sha256"]
    assert hashlib.sha256(expected).hexdigest() == expected_hash


def test_data_contract():
    """Verify the loaded dataset satisfies all domain constraints."""
    assert len(DF) == 10000
    assert QUALITY["invalid"] == 0
    assert DF["incident_id"].is_unique
    assert DF["simulated_data_flag"].all()
    assert (DF["fatalities"] <= DF["casualties"]).all()
    assert (DF.loc[DF["severity"] == "Fatal", "fatalities"] >= 1).all()
    assert (DF.loc[DF["severity"] != "Fatal", "fatalities"] == 0).all()
    assert DF["latitude"].between(30.69, 30.77).all()
    assert DF["longitude"].between(76.73, 76.83).all()


def test_validation_retains_issues():
    """Ensure invalid rows are captured in the quality log with field and reason."""
    raw = pd.read_csv(INCIDENTS_PATH).iloc[:6].copy()
    raw.loc[0, "latitude"] = 91.0
    raw.loc[1, "severity"] = "invented"
    raw.loc[2, "fatalities"] = 100
    raw.loc[3, "incident_datetime"] = "invalid"
    raw.loc[4, "incident_id"] = raw.loc[5, "incident_id"]

    clean, q = validate(raw, DF["area_name"].unique())
    assert q["invalid"] == 6
    assert len(clean) == 0
    assert q["duplicate_ids"] == 2
    flagged_fields = {issue["field"] for issue in q["issues"]}
    assert {"latitude", "severity", "casualties", "incident_datetime", "incident_id"} <= flagged_fields


def test_validation_missing_column():
    """Ensure missing columns in input data are detected immediately."""
    clean, q = validate(pd.DataFrame({"incident_id": ["x"]}), [])
    assert clean.empty
    assert "latitude" in q["missing_columns"]


def test_metrics_reconcile():
    """Verify internal mathematical consistency across aggregates."""
    f = Filters()
    results = aggregate(DF, f)
    metrics = results["metrics"]

    assert sum(metrics["severity"].values()) == metrics["count"] == 10000
    expected_burden = (
        3 * metrics["severity"]["Fatal"]
        + 2 * metrics["severity"]["Serious"]
        + metrics["severity"]["Minor"]
    )
    assert metrics["weighted_score"] == expected_burden
    assert sum(r["count"] for r in results["monthly"]) == 10000
    assert sum(r["count"] for r in results["grid"]) == 10000
    assert sum(r["weighted_score"] for r in results["areas"]) == metrics["weighted_score"]
    assert results["areas"][-1]["cumulative_share"] == 100.0


def test_fixed_metric_grid():
    """Verify 500m cell polygon coordinates and spatial invariance."""
    cell = grid(DF)[0]
    xy = [FORWARD.transform(lon, lat) for lat, lon in cell["polygon"]]

    # Edge lengths must equal 500m in UTM 43N
    assert np.isclose(np.linalg.norm(np.array(xy[0]) - xy[1]), 500, atol=0.001)
    assert np.isclose(np.linalg.norm(np.array(xy[1]) - xy[2]), 500, atol=0.001)

    # Subsets must preserve identical cell geometry
    fatal_grid = grid(DF[DF["severity"] == "Fatal"])
    matching_fatal_cell = next(r for r in fatal_grid if r["id"] == cell["id"])
    assert matching_fatal_cell["polygon"] == cell["polygon"]


def test_combined_filter_and_inclusive_end():
    """Verify multi-criteria filters with inclusive date range."""
    f = Filters(
        start="2025-01-01",
        end="2025-01-31",
        severity="Fatal",
        period="Night",
        vehicle="Car",
    )
    d = filtered(f)
    assert len(d) > 0
    assert (d["severity"] == "Fatal").all()
    assert d["night"].all()
    assert (d["vehicle_type"] == "Car").all()
    assert (d["dt"] >= pd.Timestamp("2025-01-01")).all()
    assert (d["dt"] < pd.Timestamp("2025-02-01")).all()


def test_emerging_guardrails():
    """Verify 90-day comparison window thresholds for emerging hotspots."""
    e = emerging(DF, Filters())
    assert e["windows"]["available"]
    for c in e["cells"]:
        if c["emerging"]:
            assert c["baseline"] >= 5
            assert c["recent"] >= 10
            assert c["delta"] >= 5
            assert c["ratio"] >= 1.5
        if c["baseline"] == 0:
            assert c["ratio"] is None
            assert not c["emerging"]

    short_filter = Filters(start="2026-06-01")
    assert not emerging(filtered(short_filter), short_filter)["windows"]["available"]


def test_empty_safe():
    """Verify safe degradation and null handling when no records match."""
    f = Filters(
        start="2024-07-01",
        end="2024-07-01",
        area=DF["area_name"].iloc[0],
        severity="Fatal",
        vehicle="Bus",
    )
    d = filtered(f)
    a = aggregate(d, f)
    assert len(d) == 0
    assert a["metrics"]["weighted_score"] == 0
    assert a["grid"] == []
    assert a["comparison"]["percent"] is None
    assert simulate(d, f, "Speed management", 1.0, 12, 0.5, 0.1)["projected"] == 0.0


@pytest.mark.parametrize("kind", list(INTERVENTIONS))
def test_scenarios_deterministic_bounded(kind):
    """Verify simulation determinism and bounds across all 6 interventions."""
    f = Filters()
    sim1 = simulate(DF, f, kind, 0.7, 12, 0.25, 0.1)
    sim2 = simulate(DF, f, kind, 0.7, 12, 0.25, 0.1)
    assert sim1 == sim2
    assert 0 <= sim1["projected"] <= sim1["baseline"]
    assert sim1["range"][0] <= sim1["projected"] <= sim1["range"][1]
    assert 0 <= sim1["projected_weight"] <= sim1["baseline_weight"]

    zero_sim = simulate(DF, f, kind, 0.0, 12, 1.0, 0.1)
    assert zero_sim["reduction"] == 0.0
    assert zero_sim["illustrative_cost_inr"] == 0

    double_sim = simulate(DF, f, kind, 0.7, 24, 0.25, 0.1)
    assert abs(double_sim["reduction"] - sim1["reduction"] * 2) < 0.002


@pytest.mark.parametrize(
    "query",
    [
        "start=bad",
        "start=2026-07-01",
        "start=2026-01-01&end=2025-01-01",
        "severity=unknown",
        "area=__proto__",
        "cell=999_999",
        "period=Evening",
    ],
)
def test_invalid_filters(query):
    """Ensure invalid filter parameters return HTTP 422 Unprocessable Entity."""
    response = client.get("/api/analysis?" + query)
    assert response.status_code == 422


def test_api_single_origin_and_security():
    """Verify health, security headers, CSP, and restricted endpoints."""
    assert client.get("/health").json()["rows"] == 10000

    root_resp = client.get("/")
    assert root_resp.status_code == 200
    assert "SYNTHETIC DEMONSTRATION DATA" in root_resp.text
    assert "default-src 'self'" in root_resp.headers["content-security-policy"]

    for path in ["/static/app.js", "/static/roads.geojson", "/api/meta", "/api/analysis", "/api/dossier"]:
        assert client.get(path).status_code == 200

    # Verify that data files and source files are not publicly accessible
    assert client.get("/data/incidents.csv").status_code == 404
    assert client.get("/data/synthetic/incidents.csv").status_code == 404
    assert client.get("/static/../backend/main.py").status_code == 404


def test_exports_match_filtered_state():
    """Verify CSV and PDF exports match active filter parameters."""
    query = "severity=Fatal&start=2025-01-01&end=2025-12-31&period=Night"
    count = client.get("/api/analysis?" + query).json()["metrics"]["count"]

    csv_resp = client.get("/api/export/incidents.csv?" + query)
    csv_df = pd.read_csv(io.BytesIO(csv_resp.content))
    assert len(csv_df) == count
    assert (csv_df["severity"] == "Fatal").all()
    assert csv_df["data_mode"].str.contains("SYNTHETIC").all()

    hotspots_resp = client.get("/api/export/hotspots.csv?" + query)
    hotspots_df = pd.read_csv(io.BytesIO(hotspots_resp.content))
    assert hotspots_df["count"].sum() == count

    pdf_resp = client.get("/api/export/report.pdf?" + query)
    assert pdf_resp.status_code == 200
    assert pdf_resp.content.startswith(b"%PDF-")
    assert int(pdf_resp.headers["x-filtered-count"]) == count
    assert len(pdf_resp.content) > 5000


def test_scenario_api_validation():
    """Verify POST /api/scenario payload validation rules."""
    assert client.post("/api/scenario", json={"intensity": 1.1}).status_code == 422
    assert client.post("/api/scenario", json={"months": 0}).status_code == 422
    assert client.post("/api/scenario", json={"effectiveness": -1.0}).status_code == 422
    assert client.post("/api/scenario", json={"intervention": "magic"}).status_code == 422
    assert client.post("/api/scenario", json={}).json()["mode"] == "hypothetical"


def test_validation_period_and_missing_value_audit():
    """Audit invalid datetime and missing value rejection."""
    raw = pd.read_csv(INCIDENTS_PATH).iloc[:2].copy()
    raw.loc[0, "incident_datetime"] = "2030-01-01T10:00:00"
    raw.loc[1, "vehicle_type"] = None

    clean, q = validate(raw, DF["area_name"].unique())
    assert clean.empty
    assert q["invalid"] == 2
    assert q["missing_values"]["vehicle_type"] == 1
    assert any(i["reason"] == "outside documented dataset period" for i in q["issues"])


def test_emerging_known_counts_and_zero_baseline():
    """Verify emerging hotspot window edge cases with controlled counts."""
    sample = pd.concat([DF.iloc[[0]]] * 26, ignore_index=True)
    sample.loc[:5, "dt"] = pd.Timestamp("2026-02-01")
    sample.loc[6:, "dt"] = pd.Timestamp("2026-05-01")

    e = emerging(sample, Filters())["cells"][0]
    assert e["baseline"] == 6 and e["recent"] == 20 and e["delta"] == 14 and e["emerging"]

    sample["dt"] = pd.Timestamp("2026-05-01")
    e_zero = emerging(sample, Filters())["cells"][0]
    assert e_zero["baseline"] == 0 and e_zero["ratio"] is None and not e_zero["emerging"]


def test_empty_exports_and_pdf_remain_valid():
    """Verify empty filter export responses retain valid headers and structures."""
    query = f"start=2024-07-01&end=2024-07-01&severity=Fatal&vehicle=Bus&area={DF['area_name'].iloc[0]}"
    params = dict(p.split("=", 1) for p in query.split("&"))

    for kind in ["incidents.csv", "areas.csv", "hotspots.csv"]:
        resp = client.get("/api/export/" + kind, params=params)
        assert resp.status_code == 200
        assert pd.read_csv(io.BytesIO(resp.content)).empty

    pdf_resp = client.get("/api/export/report.pdf", params=params)
    assert pdf_resp.content.startswith(b"%PDF-")
    assert pdf_resp.headers["x-filtered-count"] == "0"


def test_compression_and_revalidation_headers():
    """Verify GZip response compression and caching headers."""
    resp = client.get("/api/incidents?limit=10000", headers={"Accept-Encoding": "gzip"})
    assert resp.headers["content-encoding"] == "gzip"
    assert resp.headers["cache-control"] == "no-store"
    assert len(resp.json()["rows"]) == 10000

    root_resp = client.get("/")
    assert root_resp.headers["cache-control"] == "no-cache"
    assert "geolocation=()" in resp.headers["permissions-policy"]
