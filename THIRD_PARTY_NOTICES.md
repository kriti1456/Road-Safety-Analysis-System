# Attribution and licenses

## Conceptual reference: C.R.A.S.H

Chennai Road Accident Safety Hub by abivan100-stack:
https://github.com/abivan100-stack/C.R.A.S.H

Inspected on 2026-10-22 at commit `ed56edfbff694e7e789127c9eb1b5dd7256c5d8e`.
Reviewed README, DESIGN_LANGUAGE.md, backend/main.py, backend/requirements.txt,
shared/constants.js, shared/engine.js, intervention-model.js, report.js, dataset
schema and repository layout. Its README declares: "MIT - developed for
educational and demonstration purposes." No standalone LICENSE file was present
at that commit, so there is no verified copyright/license grant text to reproduce.

This implementation independently writes all application source, design,
generation, validation, analytics, scenarios and exports. No repository code,
fonts, assets or crash data were copied into the shipped application. Conceptual
inspiration includes severity-weighted grid rankings, area investigation and
explicit scenario eligibility. Rather than adapting the degree-based client grid,
this application uses a metric UTM backend with a shared API for all outputs.
The local reference clone under work/reference is research material and excluded
from the distribution. No claim is made that its original algorithms or synthetic
Chennai records describe Chandigarh.

## OpenStreetMap

© OpenStreetMap contributors. https://www.openstreetmap.org/copyright
Open Data Commons Open Database License (ODbL) 1.0:
https://opendatacommons.org/licenses/odbl/1-0/

`data/osm-road-source.json`, `data/anchors.json`, `static/roads.geojson` and
`data/geography-provenance.json` contain an OSM-derived extract and are distributed
under ODbL 1.0. The generator's location and anchor-name fields in
`data/incidents.csv` derive from that database. The synthetic dataset is also
made available under ODbL 1.0 to preserve those database obligations. No rights
are claimed over the underlying OSM data. A machine-readable copy of the extract
is supplied, not merely images. Nongeographical crash attributes are invented.

Actual retrieval used nine 0.02-degree map requests from the OSM v0.6 API over
76.75-76.81 E, 30.70-30.76 N on 2026-10-22. Complete named primary, secondary,
trunk and tertiary ways were retained. Earlier Overpass requests failed; no data
from those failed requests is represented as a source. See the provenance JSON
and scripts/fetch_geography.py. The displayed study extent is wider and is not
an official Chandigarh boundary. Optional online tiles use the standard OSM
server; comply with https://operations.osmfoundation.org/policies/tiles/ for any
public deployment. Default local geometry does not request tiles.

## Leaflet 1.9.4

Copyright (c) 2010-2023, Vladimir Agafonkin; Copyright (c) 2010-2011, CloudMade.
BSD 2-Clause. Actual upstream license: static/licenses/Leaflet.txt.
Source: https://github.com/Leaflet/Leaflet/tree/v1.9.4
Vendored JS/CSS from https://unpkg.com/leaflet@1.9.4/dist/.

## Chart.js 4.4.8

Copyright (c) 2014-2025 Chart.js Contributors. MIT.
Actual upstream license: static/licenses/ChartJS.txt.
https://github.com/chartjs/Chart.js/tree/v4.4.8
Vendored UMD JS from jsDelivr.

## Fonts

DM Sans (Colophon Foundry) and Barlow Condensed (Jeremy Tribby): SIL Open Font
License 1.1. Exact upstream copyright and license notices:
static/licenses/DMSans.txt and static/licenses/BarlowCondensed.txt.
Obtained from the official google/fonts repository; fonts are served locally.

## Python dependencies

FastAPI (MIT), Uvicorn (BSD-3-Clause), Pandas (BSD-3-Clause), NumPy (BSD-3-Clause),
pyproj (MIT, including PROJ data licenses), ReportLab (BSD-style) and their
transitive dependencies retain their package license notices. Installations
include those notices. requirements.lock records the environment tested here.
Test-only packages include pytest, HTTPX and Playwright.
