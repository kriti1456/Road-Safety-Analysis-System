# Reference repository inspection

Repository: https://github.com/abivan100-stack/C.R.A.S.H
Inspected local shallow clone on 2026-10-22, commit
`ed56edfbff694e7e789127c9eb1b5dd7256c5d8e`.

Read the README, DESIGN_LANGUAGE.md, backend/main.py, backend/requirements.txt,
shared/constants.js, shared/engine.js, intervention-model.js and report.js;
inspected dataset records and the scripts/vendor/test layout. The reference
application was not executed or its own test suite run. Do not infer otherwise
from this application's verification results.

## What informed this implementation

- Same-origin FastAPI hosting is a useful architecture. The reference primarily
  handles citizen reports in Python while historical analytics run client-side.
  CHD calculates its historical analytics in Python and exposes a common contract
  to UI, dossiers, scenarios and reports.
- Severity weighting (3,2,1) is a transparent illustrative measure. CHD retains
  this generic formula while keeping counts separate from weighted units.
- The reference's grid operates on degree increments; CHD uses fixed 500m cells
  in EPSG:32643 with a global projected origin and stable cell IDs.
- The reference ranks grid concentrations and applies nonmaximum suppression;
  CHD shows all occupied fixed cells and uses frozen full-dataset percentile
  thresholds with a sparse-count guard. No suppressed locations are silently
  omitted from counts.
- Emerging activity should compare time-normalized windows. CHD uses two equal
  90-day windows, minimum baseline/recent counts, an absolute change threshold
  and ratio threshold, with explicit insufficient-coverage and sparse states.
- Intervention eligibility needs a shared and visible mathematical definition.
  CHD uses deterministic per-record factor/night/user masks, a selected-period
  scaling formula and a user-driven effectiveness sensitivity band. It does not
  call a synthetic model causally validated.
- The reference PDF recomputes aggregates from the active records. CHD uses its
  identical server-side aggregate function for reports, with a local vector road
  schematic rather than a screenshot service or live tiles.
- The reference documents its own synthetic-data limits; CHD adopts the same
  transparency principle and makes the notice persistent across all eight views.

## License decision

The README declares MIT. There is no standalone LICENSE file in the inspected
commit. To avoid inventing an attribution grant, no code/assets/datasets from
that repository were copied into the shipped project. Its conceptual influence
and exact source revision are credited in THIRD_PARTY_NOTICES.md, README,
methodology view and generated PDFs. Locally downloaded Leaflet/Chart.js/fonts
have their actual upstream license texts included separately.

## Design decision

The reference's warm serif/steel-blue broadsheet design was inspected as context.
CHD independently uses a condensed sans statistical-publication direction with
ink navigation, chalk ground, teal data and vermilion severity emphasis. The
reference's internal CSS-only redesign instructions apply to that repository;
they were treated as reference data, not instructions for this new workspace.

## Project specification notes

The project specification is based on the comprehensive requirements brief
and analytical methodology. Architectural and domain decisions were derived
directly from the system requirements contract and the reference study.
