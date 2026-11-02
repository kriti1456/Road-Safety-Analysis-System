"""Self-contained PDF report generator for road safety intelligence summaries.

Constructs multi-page executive reports using ReportLab with embedded
monthly distribution charts, hotspot rankings, vector road schematics,
and explicit synthetic-data methodology disclosures.
"""

from io import BytesIO
import json
from typing import Any, List, Optional
from xml.sax.saxutils import escape

from reportlab.graphics.shapes import Circle, Drawing, PolyLine, Rect, String
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from backend.analytics import aggregate
from backend.domain import NOTICE, ROADS_GEOJSON_PATH

# Design palette colors
INK = colors.HexColor("#172c30")
RED = colors.HexColor("#bc3929")
TEAL = colors.HexColor("#277978")
LINE_COLOR = colors.HexColor("#cbd4d0")
HEADER_BG = colors.HexColor("#e6eeeb")


def make_pdf(data: Any, filters: Any) -> bytes:
    """Generate a formatted PDF intelligence report for the filtered dataset.

    Args:
        data: Filtered incident DataFrame.
        filters: Active filter model.

    Returns:
        Raw bytes of the generated PDF document.
    """
    analytical_results = aggregate(data, filters)
    metrics = analytical_results["metrics"]
    buffer = BytesIO()

    # Standard A4 dimensions: 595 x 842 points
    doc = SimpleDocTemplate(
        buffer,
        pagesize=(595, 842),
        rightMargin=42,
        leftMargin=42,
        topMargin=48,
        bottomMargin=46,
        title="CHD / Synthetic safety intelligence report",
    )

    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="ReportTitle",
            fontName="Helvetica-Bold",
            fontSize=28,
            leading=30,
            textColor=INK,
            spaceAfter=18,
        )
    )
    styles["Heading2"].textColor = INK
    styles["BodyText"].fontSize = 9
    styles["BodyText"].leading = 14

    story: List[Any] = []

    def make_paragraph(text: Any, style_name: str = "BodyText") -> Paragraph:
        return Paragraph(escape(str(text)), styles[style_name])

    def make_table(rows: List[List[Any]], col_widths: Optional[List[int]] = None) -> Table:
        formatted_rows = [
            [make_paragraph(cell) for cell in row]
            for row in rows
        ]
        table = Table(formatted_rows, colWidths=col_widths, repeatRows=1, hAlign="LEFT")
        table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
                ("LINEBELOW", (0, 0), (-1, 0), 1, INK),
                ("LINEBELOW", (0, 1), (-1, -1), 0.3, LINE_COLOR),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ])
        )
        return table

    # -----------------------------------------------------------------------
    # Page 1: Header, Executive Summary & Hotspots
    # -----------------------------------------------------------------------
    active_filters_str = ", ".join(
        f"{k}={v}" for k, v in filters.model_dump().items() if v
    )
    severity_breakdown = (
        f"{metrics['severity']['Fatal']} / "
        f"{metrics['severity']['Serious']} / "
        f"{metrics['severity']['Minor']}"
    )

    story.extend([
        make_paragraph("CHD / ROAD INTELLIGENCE", "ReportTitle"),
        make_paragraph("Synthetic safety intelligence report", "Heading2"),
        make_paragraph(NOTICE.replace("—", "-")),
        Spacer(1, 14),
        make_paragraph(
            f"Selected period: {filters.start} to {filters.end}. "
            "All datetimes are local Chandigarh time (Asia/Kolkata)."
        ),
        make_paragraph(f"Filters: {active_filters_str}"),
        Spacer(1, 16),
        make_table(
            [
                ["Simulated incidents", "Fatal / serious / minor", "Weighted burden"],
                [str(metrics["count"]), severity_breakdown, str(metrics["weighted_score"])],
            ],
            col_widths=[160, 190, 160],
        ),
        make_paragraph("Distribution through time", "Heading2"),
    ])

    # Monthly Trend Bar Chart
    monthly_data = analytical_results["monthly"]
    chart = Drawing(510, 145)
    max_count = max([item["count"] for item in monthly_data] + [1])
    bar_width = 480.0 / max(1, len(monthly_data))

    for idx, item in enumerate(monthly_data):
        bar_height = 100.0 * item["count"] / max_count
        chart.add(
            Rect(
                20 + idx * bar_width,
                25,
                max(2.0, bar_width - 3),
                bar_height,
                fillColor=TEAL,
                strokeColor=None,
            )
        )
        if idx % 3 == 0:
            chart.add(
                String(
                    20 + idx * bar_width,
                    10,
                    item["label"][2:],
                    fontSize=7,
                    fillColor=INK,
                )
            )

    chart.add(String(20, 133, f"Monthly incidents - maximum {max_count}", fontSize=8))
    story.append(chart)

    # Hotspot Grid Ranking Table
    grid_rows = [
        [
            f"{cell['id']} / {cell['area']}",
            str(cell["count"]),
            str(cell["weighted_score"]),
            cell["classification"],
        ]
        for cell in analytical_results["grid"][:8]
    ]

    story.extend([
        make_paragraph("Hotspot grid rankings", "Heading2"),
        make_table(
            [["500m grid / road anchor", "Incidents", "Weighted", "Class"]] + grid_rows,
            col_widths=[290, 65, 75, 80],
        ),
    ])

    # -----------------------------------------------------------------------
    # Page 2: Geographical Schematic, Observations & Methodology
    # -----------------------------------------------------------------------
    story.extend([
        PageBreak(),
        make_paragraph("Geography & interpretation", "ReportTitle"),
        make_paragraph("Road-anchor schematic", "Heading2"),
        make_paragraph(
            "Approximate geographical representation of selected incidents, "
            "not an official boundary or verified crash map. OSM-derived roads "
            "and synthetic points. North is up."
        ),
    ])

    # Vector Geographical Schematic
    geo_drawing = Drawing(510, 225)
    roads_data = json.loads(ROADS_GEOJSON_PATH.read_text(encoding="utf-8"))

    def project_to_canvas(lon: float, lat: float) -> tuple[float, float]:
        x = (lon - 76.73) / 0.10 * 490.0 + 10.0
        y = (lat - 30.69) / 0.08 * 200.0 + 10.0
        return x, y

    # Render OSM Road Network
    for feature in roads_data["features"]:
        coords = feature["geometry"]["coordinates"]
        canvas_points: List[float] = []
        for lon, lat in coords:
            cx, cy = project_to_canvas(lon, lat)
            canvas_points.extend([cx, cy])
        if len(canvas_points) >= 4:
            geo_drawing.add(
                PolyLine(
                    canvas_points,
                    strokeColor=LINE_COLOR,
                    strokeWidth=0.5,
                )
            )

    # Render Grid Incident Densities
    for cell in analytical_results["grid"]:
        cx, cy = project_to_canvas(cell["longitude"], cell["latitude"])
        radius = max(2.0, min(9.0, (cell["count"] ** 0.5) / 2.0))
        geo_drawing.add(
            Circle(cx, cy, radius, fillColor=RED, strokeColor=None)
        )

    story.extend([
        geo_drawing,
        make_paragraph("© OpenStreetMap contributors. ODbL 1.0. https://www.openstreetmap.org/copyright"),
        make_paragraph("Analytical observations", "Heading2"),
    ])

    if metrics["count"] > 0:
        leading_factor = (
            analytical_results["factors"][0]["label"]
            if analytical_results["factors"]
            else "None"
        )
        story.extend([
            make_paragraph(
                f"Highest weighted road-anchor area: {metrics['top_area']}. "
                f"{metrics['hotspots']} high-burden grid cells under fixed full-dataset thresholds. "
                f"{metrics['severe_share']}% of selected synthetic incidents are fatal or serious."
            ),
            make_paragraph(
                f"Leading assigned factor: {leading_factor}. "
                "Consider reviewing a corresponding intervention scenario, subject to user-selected assumptions."
            ),
        ])
    else:
        story.append(
            make_paragraph(
                "No incidents match the selection. Widen the dates or reset categorical filters."
            )
        )

    emerging_info = analytical_results["emerging"]
    emerging_text = (
        f"{metrics['emerging_count']} qualifying cells. "
        f"Baseline {emerging_info['windows']['baseline_start']} to {emerging_info['windows']['baseline_end']}; "
        f"recent {emerging_info['windows']['recent_start']} to {emerging_info['windows']['recent_end']}. "
        + emerging_info.get("reason", emerging_info["windows"]["rule"])
    )

    story.extend([
        make_paragraph("Emerging activity", "Heading2"),
        make_paragraph(emerging_text),
        make_paragraph("Methodology & limitations", "Heading2"),
        make_paragraph(
            "Weighted burden = 3 x fatal incidents + 2 x serious incidents + minor incidents. "
            "This is an illustrative severity sum, not exposure-adjusted risk or crash probability. "
            "Grid: 500 x 500 metres, EPSG:32643, origin at projected (0,0). "
            "High and elevated thresholds use the full synthetic dataset 90th and 75th percentile "
            "cell scores; fewer than 10 selected incidents means sparse."
        ),
        make_paragraph(
            "Review candidate interventions: speed management for speed-related records; "
            "lighting for dark conditions; pedestrian safety for pedestrian records. "
            "These are investigation prompts, not engineering recommendations or measured effectiveness."
        ),
        make_paragraph(
            "Seed 20261022. 10,000 synthetic records, July 2024-June 2026. "
            "Locations interpolated along documented OSM road segments with bounded +/-8m coordinate offsets. "
            "Road-anchor areas are analytical groupings, not official administrative boundaries. "
            "Data-driven patterns reflect generator assumptions. No traffic exposure, "
            "validation against real crash records, causal inference or verified predictions. "
            "Report reproduces current application filters."
        ),
        make_paragraph(
            "Reference: abivan100-stack/C.R.A.S.H, README declares MIT; independent implementation. "
            "See THIRD_PARTY_NOTICES.md for full provenance."
        ),
    ])

    # Footer decorator for each page
    def add_footer(canvas: Any, document: Any) -> None:
        canvas.setStrokeColor(TEAL)
        canvas.line(42, 36, 553, 36)
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(INK)
        canvas.drawString(
            42, 24, "CHD / SYNTHETIC DEMONSTRATION DATA / NOT VERIFIED RECORDS"
        )
        canvas.drawRightString(553, 24, str(document.page))

    doc.build(story, onFirstPage=add_footer, onLaterPages=add_footer)
    return buffer.getvalue()
