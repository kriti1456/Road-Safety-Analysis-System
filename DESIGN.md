---
name: "CHD / Road Intelligence"
description: "An independent statistical publication for exploring synthetic road-safety evidence."
colors:
  ink: "#172c30"
  paper: "#f3f4ed"
  surface: "#fcfcf7"
  muted: "#516265"
  line: "#ccd2c8"
  teal: "#216b69"
  red: "#bc3929"
  amber: "#9b6418"
  cyan: "#c0dfda"
  category-blue: "#49648a"
  category-olive: "#52643e"
  category-plum: "#8b5573"
  nav-active: "#d6e5d8"
  nav-hover: "#294348"
  notice: "#e4b96b"
  notice-ink: "#302917"
  panel-insight: "#dfe9df"
  panel-inspector: "#e5eae0"
  panel-scenario: "#e2e9df"
  map-ground: "#dfe8df"
  chart-grid: "#dbe0d6"
typography:
  display:
    fontFamily: "Barlow, sans-serif"
    fontSize: "clamp(34px,3vw,48px)"
    fontWeight: 600
    lineHeight: 1.05
    letterSpacing: "-.025em"
  headline:
    fontFamily: "Barlow, sans-serif"
    fontSize: "24px"
    fontWeight: 600
    lineHeight: 1.1
    letterSpacing: "-.015em"
  title:
    fontFamily: "DM, sans-serif"
    fontSize: "14px"
    fontWeight: 700
  body:
    fontFamily: "DM, sans-serif"
    fontSize: "14px"
    lineHeight: 1.5
  label:
    fontFamily: "DM, sans-serif"
    fontSize: "11px"
  metric:
    fontFamily: "Barlow, sans-serif"
    fontSize: "42px"
    fontWeight: 600
    lineHeight: 1.15
    letterSpacing: "-.02em"
  scenario:
    fontFamily: "Barlow, sans-serif"
    fontSize: "65px"
    fontWeight: 600
    lineHeight: 1
rounded:
  square: "0"
  dot: "50%"
spacing:
  tight: "6px"
  small: "12px"
  medium: "18px"
  panel: "22px"
  base: "24px"
  column: "26px"
  section: "30px"
  page: "34px"
components:
  button-primary:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.paper}"
    rounded: "{rounded.square}"
    padding: "10px 15px"
    typography: "{typography.label}"
  button-primary-hover:
    backgroundColor: "#2c4f52"
  button-outline:
    backgroundColor: "transparent"
    textColor: "{colors.ink}"
    rounded: "{rounded.square}"
    padding: "10px 15px"
    typography: "{typography.label}"
  field:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.square}"
    padding: "7px 9px"
    typography: "{typography.label}"
  nav-link:
    padding: "11px 12px"
    textColor: "#d1dcd5"
  nav-active:
    backgroundColor: "{colors.nav-active}"
    textColor: "{colors.ink}"
  status:
    padding: "2px 6px"
    typography: "{typography.label}"
    rounded: "{rounded.square}"
  insight-panel:
    backgroundColor: "{colors.panel-insight}"
    padding: "22px"
  synthetic-notice:
    backgroundColor: "{colors.notice}"
    textColor: "{colors.notice-ink}"
    padding: "8px 12px"
    typography: "{typography.label}"
---

# Design System: CHD / Road Intelligence

## Overview

**Creative North Star: "The Swiss Transport Statistics Annual"**

A chalk-ground analytical publication with a deep ink navigation rail, condensed headings, and quiet ruled data regions. The visual world borrows the discipline of transport statistics: compact labels, generous titles, explicit assumptions, and a map that carries the geographical argument. It does not simulate paper texture.

The same shell serves eight analytical views. Colour makes severity and category identity durable across metrics, maps, charts, tables, and comparison. The synthetic-data notice is part of the persistent shell, because the status of the evidence must remain visible while users investigate it.

**Key Characteristics:**
- Condensed editorial hierarchy with tabular numbers.
- Square, ruled analytical regions and tonal information panels.
- Stable severity and category colours with textual labels.
- Persistent provenance and accessible chart-data tables.

## Colors

Deep ink and chalk neutrals carry the interface; vermilion, ochre, and teal carry analytical meaning. The frontmatter is the normative colour inventory.

### Primary
- **Deep Ink** (`ink`): shell, titles, rules, primary actions, selected grid outline, and formula panels.
- **Analytical Teal** (`teal`): minor severity / lower burden, ordinary time series, links, range controls, and scenario outcomes.

### Secondary
- **Vermilion** (`red`): fatal severity / high burden, ranked burden bars, and keyboard focus.
- **Ochre** (`amber`): serious severity / elevated burden.
- **Publication Notice** (`notice`, `notice-ink`): persistent evidence-status strip; separate from severity encoding.

### Tertiary
- **Category Blue, Olive, Plum**: extend the ordered category palette after teal, vermilion, and ochre. Metadata position, not the order of a filtered chart, assigns vehicle/factor colour. Road-user ordering is Driver, Rider, Pedestrian, Passenger, Cyclist. The first two series of area comparisons use teal and red by series position.
- **Pale Cyan** (`cyan`): declared incumbent token, currently unused in rendered components; do not assign it a new semantic role without a concrete need.

### Neutral
- **Chalk Ground** (`paper`): workspace and page background.
- **Warm Surface** (`surface`): fields and skip-link surface.
- **Muted Slate** (`muted`): captions, labels, and secondary reading.
- **Fine Divider** (`line`): ledgers, filters, tables, and shell boundaries.
- **Navigation Tints** (`nav-active`, `nav-hover`): active and hover fills on the ink rail.
- **Panel Tints** (`panel-insight`, `panel-inspector`, `panel-scenario`): distinct supporting information regions.
- **Map Ground** and **Chart Grid**: subdued contextual infrastructure underneath data.

**The The Stable Meaning Rule.** Fatal / high burden uses red, serious / elevated uses amber, and minor / lower uses teal. Non-severity categories retain their metadata-index colour when sorted or filtered.

## Typography

**Display Font:** locally served Barlow Condensed SemiBold, CSS alias `Barlow`, with `sans-serif` fallback.

**Body Font:** locally served DM Sans, CSS alias `DM`, with `sans-serif` fallback. Both fonts use `font-display: swap`.

**Character:** tightly condensed headings establish a publication hierarchy; DM Sans keeps dense controls and caveats readable. Body numbers use tabular figures. There is no distinct monospaced label family.

### Hierarchy
- **Display:** page titles use the frontmatter clamp; at the 850px breakpoint they become 46px and at 560px, 40px. The brand is a separate 41px condensed wordmark, stepping to 34px and 30px.
- **Headline:** section headings use the headline token; mobile reduces them to 27px.
- **Title:** compact DM Sans bold titles. Inspector headings use condensed 25px instead.
- **Body:** the base token governs reading. Methodology paragraphs use 13px with a 75ch maximum; insight paragraphs use 12px with a 70ch maximum.
- **Label:** static labels, tables, controls, captions, legend text, map annotations, and chart summaries commonly use 11px. Navigation uses 13px, then 12px below 1150px. Compact supporting reading also uses 12px.
- **Metric:** the frontmatter metric role steps to 35px below 1150px, 34px below 850px, then 36px in the mobile ledger. The full-width mobile total uses 52px. Scenario results use the scenario token, reducing to 56px below 560px.
- **Canvas labels:** chart axes and comparison legends explicitly use 11px; ordinary-chart axes use DM, and the global Chart.js family is `DM, sans-serif`. These are canvas settings, not CSS type tokens.

**The The Two Type Voices Rule.** Use Barlow Condensed for headings and analytical numbers; use DM Sans for reading, controls, labels, and tables. Keep canvas tick and legend labels at the shipped 11px size.

## Layout

A fixed ink rail (226px) anchors a chalk workspace. Main content has 32px 34px 48px padding and an 1800px maximum width. A sticky synthetic notice sits above the 53px topbar. Shared filters wrap inside two horizontal rules, followed by a selection-state line. The desktop metrics ledger is one 1.35fr cell and four equal cells. Analytical two-column sections use a 1.8fr dominant panel and a minimum 270px supporting panel; equal comparison/chart columns use equal fractions. Column gaps are normally 26px. Sections begin after 30px; common panel inset is 22px.

- **1600px and wider:** rail and workspace offset become 245px, main padding becomes 38px 46px, and ordinary maps are 480px high.
- **1150px and narrower:** rail becomes 190px with 25px 16px padding; main uses 25px 24px; the dominant grid becomes 1.45fr / minimum 240px, with a 20px gap. Edition text disappears.
- **850px and narrower:** rail enters normal document flow, geography/footer copy disappears, and navigation becomes a horizontally scrolling row of text links with 40px minimum height. Workspace offset clears; main analytical columns stack. Equal chart/comparison columns remain paired until 560px. Ordinary maps become 420px and explorer maps 480px.
- **560px and narrower:** main uses 24px 18px; filters form a two-column grid; the ledger total spans the row above a two-column remainder; all analytical columns stack. Ordinary/explorer maps are 350px / 430px. The title export action retains its accessible name but shows only its SVG. Tables scroll within their own region; the footer stacks.

Ordinary maps default to 405px, explorer maps to 620px. Charts default to 225px, tall charts to 290px, and ordinary charts to 220px at the smallest breakpoint. Methodology is a restrained 850px reading column. Print hides navigation, filters, topbar, and buttons and makes the notice static.

## Elevation & Depth

The interface is flat at rest. Fine rules, dark anchors, and muted tonal panels provide separation; there are no floating card shadows. Map labels explicitly remove shadows. The toast alone uses the `ambient-toast` shadow recorded in the sidecar. Map attribution and the provenance stamp remain visibly layered over the geographical canvas.

**The The Ruled Surface Rule.** Separate analytical regions with ink rules, fine dividers, and muted tonal fills. Reserve the ambient shadow for the transient toast.

## Shapes

Analytical panels, controls, buttons, tables, and active navigation are square. Borders are typically 1px; the inspector uses a 2px top rule and area comparison panels use 3px teal/red top rules. Small circular legend dots, the status-mode dot, map markers, and the severity doughnut are semantic exceptions. Inline SVG strokes supply navigation and export icons.

## Components

### Buttons

Compact rectangular actions: primary buttons use ink and chalk, outline actions use a transparent background and an ink border. Both use the frontmatter padding, 11px semibold type, and a 38px minimum height. Primary hover becomes a lighter ink; outline hover uses a pale neutral fill. Download-row actions have a 44px minimum height. Text actions are underlined. Disabled buttons use 0.45 opacity and a waiting cursor. Keyboard focus uses a 3px vermilion outline with a 3px offset.

### Inputs / Fields

Square warm-surface fields use a muted green border, compact label text, a 36px minimum height, and the frontmatter inset. Labels sit above fields with a 5px gap. Date inputs are 127px before mobile width rules. Range inputs use teal; errors occupy a pale red alert region. Do not invent extra validation states from the tokens.

### Navigation

The ink rail has white-toned identity, muted light links, inline SVGs, and a pale selected rectangle with ink text. Hover uses the navigation-hover tint. The narrow-screen row omits the icons and scrolls horizontally. Keyboard focus follows the shared outline treatment.

### Cards / Containers

These are ruled regions and flat tonal information panels. Insight, inspector, and scenario panels each use their documented tint and 22px inset. Chart blocks begin with an ink rule and 20px vertical padding rather than a surrounding card. Ranked rows use a fine lower divider, text metadata, a right-aligned condensed score, and a vermilion burden bar; hover and selection share a pale green fill.

### Status Tags and Synthetic Notice

Severity tags are square outline labels using current colour and a 2px 6px inset. The sticky evidence-status notice uses bold 11px text with .085em tracking; its qualification breaks onto a second line below 560px. This notice communicates provenance, rather than acting as a decorative section label.

### Map and Investigation

The map carries local OSM road geometry on the muted ground even when optional tiles fail. Severity/burden layers use the same three categorical colours as the rest of the product. Selected cells gain an ink outline (3px), and selection synchronizes the ranked row and inspector. The shipped interaction jumps directly to the footprint without animation. A legend, scale, attribution, and explicit synthetic/study-extent stamp remain adjacent to the data.

### Charts and Data Tables

Bars, lines, and doughnuts share stable colours; time lines use 2px strokes, 2px points, .25 tension, and no fill. Standard and comparison multi-series chart animations last 350ms and are disabled when reduced motion is requested. Every chart is accompanied by a readable summary and an expandable data table. Tables use 11px text, ink header rules, fine body dividers, and a local horizontal scrolling wrapper. Open chart-data regions cap at 280px with scrolling.

The content reveal is a 300ms ease-out blur resolution; reduced motion removes it, disables smooth page scrolling, and suppresses Leaflet zoom transitions. Map construction independently disables zoom/fade/marker animations. Controls have immediate hover-state changes rather than decorative transitions.

## Do's and Don'ts

### Do:
- **Do** keep the synthetic-data notice visible across all eight views.
- **Do** preserve severity colour meanings and label each meaning in text.
- **Do** accompany charts with readable summaries and expandable data tables.
- **Do** stack analytical columns and allow local table/navigation scrolling on narrow screens.
- **Do** keep attribution, study-extent qualifications, and selected-cell identity attached to the map.

### Don't:
- **Don't** introduce rounded card stacks or ambient shadows to resting analytical regions.
- **Don't** turn canvas chart labels into a second display typeface.
- **Don't** add decorative uppercase kickers above section headings.
- **Don't** imply that synthetic counts or hypothetical outcomes are verified risk or causal forecasts.

<!-- Evidence: static/style.css, static/index.html, static/app.js; PRODUCT.md and .impeccable/direction.md; rendered review desktop.png and mobile-intervention.png. The review directory contains desktop/mobile captures for all eight views. Standard and comparison multi-series charts both honor reduced motion; no implementation was changed in this documentation handoff. -->

## Minimal presentation (user revision)

The user requested removal of unnecessary text and a minimal design. Page names
and navigation are now plain and short. The repeated topbar, footer, sidebar
coordinates/tagline, page subtitles, empty inspector prompts, overview caution
callout, and numeric chart-summary paragraphs are removed. The overview now
focuses on metrics, map/rankings, monthly/factor charts and emerging activity;
other distributions and incident browsing remain in their dedicated views.

Keep one persistent full synthetic-data notice. Preserve map attribution, labels,
units and concise scenario/exposure caveats. Put chart context behind Data, model
explanation behind Model details, and technical methodology behind individual
expandable sections. Avoid adding explanatory copy that repeats visible controls
or values. Inspectors appear only after selecting a location. Page headings now
cap at 48px, section headings use 24px, and secondary panels use plain surfaces.

Additional filters are grouped in a native Filters disclosure with a count of
active categorical filters. Dates and area remain visible. All fields continue
to participate in the shared form and filter-sensitive exports.

## Interaction hardening — 23 October 2026

Preserve the minimal editorial identity. Controls use a 44px minimum and 13px labels;
phone form inputs use 16px to avoid focus zoom. Maps place synthetic-location context
and legends in normal document flow. Requests show a restrained progress line and
brief opacity acknowledgment; scenario results acknowledge a completed calculation.
All movement and chart animation respect reduced motion. Navigation, download,
error, disabled, selected and keyboard states use the same ink/teal palette.

Requests time out after 30 seconds, cancel on view/filter changes, and reject stale
responses. Download links prepare blobs with visible feedback and preserve the
workspace on failure. Chart Data disclosures expose keyboard filter controls.
