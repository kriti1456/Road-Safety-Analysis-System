# Verification record

Verified locally on 2026-10-22 using Python 3.13.7 and real headless Chromium.

## Automated backend suite

28 tests passed. Includes byte-for-byte 10,000-row regeneration and manifest hash,
invalid-record audit, schema/missing columns/period/missing-value audit, fixed 500m UTM cell dimensions and
filter stability, metric reconciliation, inclusive combined filters, emerging
threshold guardrails and short-window state, safe empty results, all six scenario
models (determinism/bounds/zero intensity/duration scaling), seven invalid-filter
cases, same-origin static handling, response security headers, state-sensitive
CSV and PDF responses, and scenario request validation.

One upstream Starlette TestClient/HTTPX deprecation warning is emitted by the
pinned environment. No test failures were suppressed.

## Real browser verification

`tests/browser_flows.py` runs the actual app on http://127.0.0.1:8765. Its latest
completed results are in `docs/browser-results.json`. Checks include eight-view
navigation, ranked map selection to cell dossier, incident/density/emerging
layers, incident popups, table pagination, severity-filter reconciliation,
analytics/sort interaction, comparison area selection, zero-intensity scenario
and JSON download, actual CSV/PDF downloads, methodology preview, mobile overflow,
empty selection and reset recovery. A final matrix captures all eight routes at
1440px and 390px and checks for errors and horizontal page overflow.

A Leaflet animation error under rapid navigation was found during verification.
Map removal now stops animation and selection framing uses a deterministic
immediate view transition. The full browser flow was rerun after that correction.
The harness initially used an eval-style wait incompatible with the application's
CSP; the harness was corrected to use function predicates without weakening CSP.

## PDF

The browser-downloaded state-sensitive PDF was inspected using pdfinfo and
rendered with Poppler. It contains two A4 pages with no clipped text, broken
symbols, overlapping sections or missing chart/map geometry in the reviewed
filtered state. Page 1 carries filters, counts, trend and grid rankings; page 2
contains a geographical schematic, observations, methodology and limitations.
The footer on both pages identifies synthetic data. The backend test separately
checks another filtered PDF and filtered CSV count reconciliation. Empty CSV/PDF exports and a controlled emerging-window example are also tested.

## Scope of claims

No public deployment, load/endurance benchmark, Docker execution, formal WCAG
audit, real-world crash validation or causal/predictive model validation was
performed. The online tile service is optional and the stored geometry works
offline. The present geography contains selected named roads, not the complete
city network. Scenario sensitivity bands are not confidence intervals. Excel
output is not implemented. PDF is not accessibility-tagged. The system implementation follows the documented analytical requirements and design specification directly.

## Independent design review

Initial disposition: fix, for 9px canvas labels, category colors changing with
sorted comparison order, and a separate intervention eyebrow. One correction
batch raised chart labels/legends to 11px, made category colors stable, and put
hypothetical meaning into the result heading. All 16 captures were replaced
and the complete browser sequence rerun with an added color-consistency check.
The independent reviewer scored all three findings resolved, with disposition
ship. This verdict covers those three fixes; it is not a certification of
security, real-world analytical validity or formal accessibility compliance.
See docs/design-review.md for the evidence and scoped verdict.

Documentation also identified a comparison-chart reduced-motion omission. It was
corrected to the same 350ms-or-disabled policy as standard charts. A targeted real
Chromium check verified animation:false for both types with reduced motion, and
the affected two comparison captures were refreshed. Design documentation was
updated to match.

## Minimal interface revision

At the user's request, repeated explanatory UI text, subtitles, numeric chart
summaries, empty inspector prompts and duplicate overview panels were removed.
Chart context, model explanations and methodology now use native expandable
sections. Additional categorical filters are grouped behind Filters; active
filter count stays visible. The full synthetic notice, geographical attribution,
controls, exports and essential model limitations remain. The existing real
browser suite was adapted for the disclosures and rerun across all eight views
at desktop/mobile widths. Prior independent design-review findings describe the
previous presentation; they are not a new review claim for this revision.

## Production hardening revision — 23 October 2026

- 29 backend tests pass, including compressed response integrity and cache/security headers.
- Eight-view Chromium flow suite passes: filters, maps, dossiers, scenarios, CSV/PDF/JSON downloads, empty recovery; 16 desktop/mobile captures, no page errors.
- Seven additional Chromium resilience checks pass: inverted dates, API failure/retry, failed exports, rapid navigation, reduced motion/live status, mobile input/legend layout, and keyboard chart filtering.
- Fixed a real Leaflet lifecycle error observed during navigation: delayed resize now checks map ownership.
- Added abort/timeout handling, recoverable downloads, 44px controls, mobile 16px inputs, keyboard chart filters, completion announcements and restrained motion.
- Large responses are gzip compressed. The HTML entry revalidates; APIs remain no-store. Security headers now also cover handled internal errors.
- CI definition includes backend, syntax, Chromium, and screenshot artifacts. Hosted CI itself has not run here.
- Still a local synthetic-data application. Public deployment, sustained load testing, external security assessment, physical-device testing and formal accessibility certification remain unverified. No authentication is added because the current application is read-only, public synthetic data with no accounts or private records.
