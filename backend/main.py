"""Single-origin FastAPI web application for Chandigarh Road Safety Intelligence.

Exposes analytical endpoints, dataset query filters, hotspot aggregations,
dossier generation, scenario simulation, state-sensitive exports,
and mounts static frontend single-page application assets.
"""

from datetime import date
import json
import logging
from typing import Annotated, Literal
import uuid

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
import pandas as pd
from pydantic import BaseModel, Field, model_validator
from pyproj import Geod
from starlette.middleware.gzip import GZipMiddleware

from backend.analytics import (
    ANCHORS,
    DF,
    Q75,
    Q90,
    QUALITY,
    aggregate,
    basic,
    filtered,
    grid,
    records,
    simulate,
)
from backend.domain import (
    END,
    FACTORS,
    GEOGRAPHY_PROVENANCE_PATH,
    INTERVENTIONS,
    MANIFEST_PATH,
    NOTICE,
    ROOT_DIR,
    START,
    STATIC_DIR,
    VEHICLES,
    WEIGHTS,
)
from backend.reports import make_pdf

# Geodetic distance calculator (WGS84 ellipsoid)
GEOD: Geod = Geod(ellps="WGS84")


class Filters(BaseModel):
    """Query parameter schema for filtering synthetic incident records."""

    start: str = START
    end: str = END
    area: str | None = None
    severity: Literal["Fatal", "Serious", "Minor"] | None = None
    vehicle: str | None = None
    factor: str | None = None
    period: Literal["All", "Day", "Night"] = "All"
    cell: str | None = None

    @model_validator(mode="after")
    def validate_filter_constraints(self) -> "Filters":
        """Validate temporal ranges and categorical membership."""
        try:
            start_date = date.fromisoformat(self.start)
            end_date = date.fromisoformat(self.end)
        except ValueError:
            raise ValueError("Dates must be YYYY-MM-DD")

        if self.start < START or self.end > END or start_date > end_date:
            raise ValueError(f"Dates must be ordered within {START} and {END}")

        allowed_areas = [anchor["name"] for anchor in ANCHORS]
        allowed_cells = DF["cell_id"].unique()

        validations = [
            (self.area, allowed_areas),
            (self.vehicle, VEHICLES),
            (self.factor, FACTORS),
            (self.cell, allowed_cells),
        ]

        for val, allowed in validations:
            if val is not None and val not in allowed:
                raise ValueError("Unknown filter category or grid cell")

        return self


def get_filters(
    start: str = START,
    end: str = END,
    area: str | None = None,
    severity: str | None = None,
    vehicle: str | None = None,
    factor: str | None = None,
    period: str = "All",
    cell: str | None = None,
) -> Filters:
    """Dependency resolver for request query filter parameters."""
    try:
        return Filters(
            start=start,
            end=end,
            area=area,
            severity=severity,  # type: ignore[arg-type]
            vehicle=vehicle,
            factor=factor,
            period=period,  # type: ignore[arg-type]
            cell=cell,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


FilterDependency = Annotated[Filters, Depends(get_filters)]


class Scenario(BaseModel):
    """Request payload schema for hypothetical counterfactual simulations."""

    filters: Filters = Field(default_factory=Filters)
    intervention: str = "Speed management"
    intensity: float = Field(default=0.7, ge=0.0, le=1.0)
    months: int = Field(default=12, ge=1, le=36)
    effectiveness: float = Field(default=0.25, ge=0.0, le=1.0)
    uncertainty: float = Field(default=0.1, ge=0.0, le=0.5)

    @model_validator(mode="after")
    def validate_intervention_name(self) -> "Scenario":
        if self.intervention not in INTERVENTIONS:
            raise ValueError("Unknown intervention")
        return self


# FastAPI Application Setup
app: FastAPI = FastAPI(
    title="Chandigarh Road Safety Intelligence System",
    description="Interactive analytical dashboard and descriptive analytics for road safety exploration.",
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
)

# GZip compression middleware for payload efficiency
app.add_middleware(GZipMiddleware, minimum_size=1000, compresslevel=5)


@app.middleware("http")
async def apply_security_headers(request: Request, call_next):
    """Attach security, cache-control, and request tracking headers."""
    request_id = uuid.uuid4().hex[:12]
    try:
        response = await call_next(request)
    except Exception:
        logging.exception("Request %s failed", request_id)
        response = JSONResponse(
            {
                "detail": "Unable to complete request. Retry or inspect server logs.",
                "request_id": request_id,
            },
            status_code=500,
        )

    response.headers.update({
        "X-Request-ID": request_id,
        "X-Content-Type-Options": "nosniff",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "X-Frame-Options": "DENY",
        "Content-Security-Policy": (
            "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https://tile.openstreetmap.org; font-src 'self'; "
            "connect-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'"
        ),
        "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    })

    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    elif request.url.path == "/":
        response.headers["Cache-Control"] = "no-cache"

    return response


@app.get("/health")
def health_check():
    """Health status and dataset readiness endpoint."""
    return {
        "status": "ok",
        "mode": "synthetic",
        "rows": len(DF),
    }


@app.get("/api/meta")
def get_metadata():
    """Return dataset manifest, taxonomies, spatial anchors, and formula parameters."""
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    geography = json.loads(GEOGRAPHY_PROVENANCE_PATH.read_text(encoding="utf-8"))

    return {
        "notice": NOTICE,
        "manifest": manifest,
        "areas": [anchor["name"] for anchor in ANCHORS],
        "anchors": ANCHORS,
        "severities": list(WEIGHTS.keys()),
        "vehicles": VEHICLES,
        "factors": FACTORS,
        "interventions": INTERVENTIONS,
        "quality": QUALITY,
        "geography": geography,
        "grid": {
            "crs": "EPSG:32643",
            "metres": 500,
            "elevated_threshold": Q75,
            "high_threshold": Q90,
            "minimum_selected_count": 10,
        },
    }


@app.get("/api/analysis")
def get_analysis(f: FilterDependency):
    """Compute and return complete analytical metrics for the active filter set."""
    filtered_df = filtered(f)
    return {
        "filters": f.model_dump(),
        "mode": "synthetic",
        **aggregate(filtered_df, f),
    }


@app.get("/api/incidents")
def get_incidents(
    f: FilterDependency,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=10000),
    sort: Literal["newest", "oldest", "severity"] = "newest",
):
    """Return paginated individual incident records matching active filters."""
    filtered_df = filtered(f)
    sort_column = "weight" if sort == "severity" else "dt"
    ascending_order = sort == "oldest"

    sorted_df = filtered_df.sort_values(sort_column, ascending=ascending_order)
    page_records = records(sorted_df.iloc[offset : offset + limit])

    return {
        "total": len(filtered_df),
        "offset": offset,
        "rows": page_records,
    }


@app.get("/api/dossier")
def get_dossier(f: FilterDependency):
    """Generate comprehensive localized dossier for a selected corridor or grid cell."""
    filtered_df = filtered(f)
    aggregated_data = aggregate(filtered_df, f)
    city_baseline = basic(DF)

    # Evaluate candidate intervention eligibility
    candidates = []
    for kind, spec in INTERVENTIONS.items():
        sim_result = simulate(filtered_df, f, kind, 0.7, 12, 0.25, 0.1)
        candidates.append({
            "intervention": kind,
            "eligible": sim_result["eligible_count"],
            "reason": spec["reason"],
        })
    candidates.sort(key=lambda r: -r["eligible"])

    # Locate nearest neighboring grid cells
    nearby_cells = []
    coordinates = None
    if len(filtered_df):
        centroid_lon = float(filtered_df["longitude"].mean())
        centroid_lat = float(filtered_df["latitude"].mean())
        coordinates = {"latitude": centroid_lat, "longitude": centroid_lon}
        selected_cells = set(filtered_df["cell_id"])

        for cell in grid(DF):
            if cell["id"] not in selected_cells:
                _, _, distance = GEOD.inv(
                    centroid_lon,
                    centroid_lat,
                    cell["longitude"],
                    cell["latitude"],
                )
                nearby_cells.append({**cell, "distance_m": round(distance)})

        nearby_cells.sort(key=lambda r: r["distance_m"])

    return {
        **aggregated_data,
        "coordinates": coordinates,
        "city_baseline": city_baseline,
        "recommendations": candidates,
        "nearby": nearby_cells[:4],
    }


@app.post("/api/scenario")
def calculate_scenario(scenario_req: Scenario):
    """Compute deterministic counterfactual projection for selected and alternative interventions."""
    filtered_df = filtered(scenario_req.filters)
    f = scenario_req.filters
    primary_result = simulate(
        filtered_df,
        f,
        scenario_req.intervention,
        scenario_req.intensity,
        scenario_req.months,
        scenario_req.effectiveness,
        scenario_req.uncertainty,
    )
    alternatives = [
        simulate(
            filtered_df,
            f,
            alt_kind,
            scenario_req.intensity,
            scenario_req.months,
            scenario_req.effectiveness,
            scenario_req.uncertainty,
        )
        for alt_kind in INTERVENTIONS
    ]

    return {
        **primary_result,
        "alternatives": alternatives,
    }


@app.get("/api/export/{kind}")
def export_dataset(
    kind: Literal["incidents.csv", "areas.csv", "hotspots.csv", "report.pdf"],
    f: FilterDependency,
):
    """Export filtered dataset records as CSV or structured PDF report."""
    filtered_df = filtered(f)

    if kind == "report.pdf":
        body = make_pdf(filtered_df, f)
        media_type = "application/pdf"
    else:
        if kind == "incidents.csv":
            export_columns = [
                col for col in DF.columns
                if col not in ["dt", "weight", "night", "gx", "gy"]
            ]
            export_df = pd.DataFrame(records(filtered_df), columns=export_columns)
        else:
            agg_results = aggregate(filtered_df, f)
            source_data = agg_results["areas" if kind == "areas.csv" else "grid"]
            export_df = pd.DataFrame(source_data).drop(columns=["polygon"], errors="ignore")

        # Guarantee fallback columns on empty selections
        if export_df.empty and len(export_df.columns) == 0:
            fallback_col = "area" if kind == "areas.csv" else "id"
            export_df = pd.DataFrame(columns=[fallback_col, "count", "weighted_score"])

        export_df["data_mode"] = "SYNTHETIC - NOT VERIFIED"
        export_df["selected_filters"] = json.dumps(f.model_dump(), sort_keys=True)
        body = export_df.to_csv(index=False, lineterminator="\n").encode("utf-8-sig")
        media_type = "text/csv"

    return Response(
        body,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="chd-synthetic-{kind}"',
            "X-Data-Mode": "synthetic",
            "X-Filtered-Count": str(len(filtered_df)),
        },
    )


@app.get("/")
def index():
    """Serve single-page frontend application entry HTML."""
    return FileResponse(STATIC_DIR / "index.html")


# Mount static assets directory
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
