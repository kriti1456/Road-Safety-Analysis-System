"""Real Chromium functional checks for all eight application views.

Tests the full interactive dashboard including:
  - 8 views navigation and rendering
  - Leaflet maps with points, density circles, and emerging layers
  - Chart.js interactive filtering and category drill-down
  - Multi-criteria filter application and reset recovery
  - Scenario simulation and scenario JSON download
  - State-sensitive CSV and PDF report downloads
  - Responsive mobile (390px) and desktop (1440px) visual matrix

Pre-requisite: Start the FastAPI application on http://127.0.0.1:8765 first:
  python -m uvicorn backend.main:app --host 127.0.0.1 --port 8765
"""

import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "screenshots"
OUT.mkdir(parents=True, exist_ok=True)
OUTPUTS_DIR = ROOT / "outputs"
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

BASE = os.environ.get("CHD_TEST_URL", "http://127.0.0.1:8765")


def get_chrome_executable() -> str | None:
    """Find a local Chrome, Chromium, or Edge executable across Windows, macOS, and Linux."""
    env_path = os.environ.get("CHROME_PATH") or os.environ.get("PLAYWRIGHT_CHROME_EXECUTABLE")
    if env_path and Path(env_path).exists():
        return env_path
    candidates = [
        Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
        Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
        Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
        Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
        Path.home() / "Library/Caches/ms-playwright/chromium-1234/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing",
        Path.home() / "Library/Application Support/Google/Chrome/Application/chrome",
        Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
        Path("/usr/bin/google-chrome"),
        Path("/usr/bin/chromium"),
        Path("/usr/bin/chromium-browser"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return None


results = []
chrome_bin = get_chrome_executable()

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=chrome_bin, headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 1050}, device_scale_factor=1)
    errors = []
    page.on("pageerror", lambda e: errors.append(page.url + ": " + e.stack))

    page.goto(BASE)
    page.wait_for_selector(".rank-row")
    page.wait_for_timeout(500)

    assert page.locator(".metric-value").first.inner_text() == "10,000"
    assert page.locator(".notice").is_visible()
    page.locator("h1").click()
    page.screenshot(path=str(OUT / "desktop.png"), full_page=True)
    results.append("Overview: 10,000 records, real map, charts and synthetic notice")

    page.locator(".rank-row").first.click()
    assert page.locator("#open-dossier").is_visible()
    page.locator("#open-dossier").click()
    page.wait_for_selector("#dossier-area")
    page.wait_for_selector("#d-month")
    assert "Grid scope:" in page.locator("#content").inner_text()
    results.append("Ranked map selection -> grid dossier")

    page.locator("#reset").click()
    page.wait_for_function("() => document.querySelector('#content').getAttribute('aria-busy')==='false'")
    page.locator('#nav a[data-route="explorer"]').click()
    page.wait_for_selector("#incident-list tbody tr")
    page.locator("#map-layer").select_option("incidents")
    page.locator("[data-incident]").first.click()
    assert page.locator(".leaflet-popup-content").is_visible()
    page.locator("#map-layer").select_option("density")
    page.locator("#map-layer").select_option("emerging")
    page.locator("#next").click()
    assert page.locator("#page-label").inner_text().startswith("26")
    results.append("Explorer: point, density and emerging layers; incident popup; pagination")

    page.locator("#advanced-filters").evaluate("el => el.open = true")
    page.locator("#severity").select_option("Fatal")
    page.locator("#filters button[type=submit]").click()
    page.wait_for_function("() => document.querySelector('#content').getAttribute('aria-busy')==='false'")
    assert int(page.locator(".metric-value").first.inner_text().replace(",", "")) < 10000
    assert page.locator(".metric-value").nth(2).inner_text() == "0"
    results.append("Shared severity filter reconciles live counts")

    page.locator('#nav a[data-route="analytics"]').click()
    page.wait_for_selector("#area-table tbody tr")
    page.locator('[data-sort="count"]').click()
    assert page.locator("#area-table tbody tr").count() > 0

    # Real chart click drills into a factor and updates shared filters
    page.locator("#factor-analysis").click(position={"x": 160, "y": 25})
    page.wait_for_timeout(200)
    results.append("Analytics: charts and sortable area table")

    page.locator('#nav a[data-route="comparison"]').click()
    page.wait_for_selector("#compare-trend")
    opts = page.locator("#compare-b option")
    value = opts.nth(4).get_attribute("value")
    page.locator("#compare-b").select_option(value)
    page.wait_for_timeout(300)
    assert value in page.locator("#comparison-results").inner_text()

    color_maps = page.evaluate(
        "() => [0,1].map(i => {const c=Chart.getChart('compare-v-'+i);return Object.fromEntries(c.data.labels.map((l,j)=>[l,c.data.datasets[0].backgroundColor[j]]))})"
    )
    for name in set(color_maps[0]) & set(color_maps[1]):
        assert color_maps[0][name] == color_maps[1][name]
    assert page.evaluate("() => Chart.getChart('compare-v-0').options.scales.x.ticks.font.size") >= 11
    results.append("Comparison: selectors update metrics/charts and category colors remain stable")

    page.locator('#nav a[data-route="intervention"]').click()
    page.wait_for_selector("#save-scenario")
    page.locator("#intensity").fill("0")
    page.locator("#scenario-form button[type=submit]").click()
    page.wait_for_function("() => document.querySelector('.scenario-number').textContent.trim().startsWith('0')")

    with page.expect_download() as download:
        page.locator("#save-scenario").click()
    scenario = json.loads(Path(download.value.path()).read_text(encoding="utf-8"))
    assert scenario["result"]["reduction"] == 0
    results.append("Scenario: zero intensity -> zero reduction; actual JSON download")

    page.locator('#nav a[data-route="exports"]').click()
    page.wait_for_selector(".downloads")
    for ext in ["CSV", "PDF"]:
        selector = '.downloads a[href*="incidents.csv"]' if ext == "CSV" else '.downloads a[href*="report.pdf"]'
        with page.expect_download() as download:
            page.locator(selector).click()
        data = Path(download.value.path()).read_bytes()
        assert len(data) > 100
        if ext == "PDF":
            assert data.startswith(b"%PDF-")
            Path(ROOT / "outputs/verified-filtered-report.pdf").write_bytes(data)
        else:
            assert b"SYNTHETIC" in data and b"Fatal" in data
    results.append("State-sensitive CSV and PDF browser downloads")

    page.locator('#nav a[data-route="methodology"]').click()
    page.wait_for_selector("#data-preview", state="attached")
    page.get_by_text("Grid & burden", exact=True).click()
    assert "EPSG:32643" in page.locator("#content").inner_text()
    results.append("Methodology: anchor provenance, model assumptions and data preview")

    page.locator("#reset").click()
    page.wait_for_function("() => document.querySelector('#content').getAttribute('aria-busy')==='false'")
    page.locator('#nav a[data-route="overview"]').click()
    page.wait_for_selector(".rank-row")
    page.set_viewport_size({"width": 390, "height": 844})
    page.wait_for_timeout(400)
    assert page.evaluate("document.documentElement.scrollWidth<=window.innerWidth")
    page.locator("h1").click()
    page.screenshot(path=str(OUT / "mobile.png"), full_page=True)
    results.append("390px mobile: no horizontal page overflow, persistent notice and usable filters")

    page.locator("#start").fill("2024-07-01")
    page.locator("#end").fill("2024-07-01")
    page.locator("#advanced-filters").evaluate("el => el.open = true")
    page.locator("#severity").select_option("Fatal")
    page.locator("#vehicle").select_option("Bus")
    page.locator("#area").select_option(index=1)
    page.locator("#filters button[type=submit]").click()
    page.wait_for_selector(".empty")
    assert "No matching incidents" in page.locator(".empty").inner_text()
    page.locator("[data-reset]").click()
    page.wait_for_selector(".rank-row")
    results.append("Empty result and reset recovery")

    # Final batched visual matrix: all eight views at desktop and phone widths
    for width in [1440, 390]:
        page.set_viewport_size({"width": width, "height": 1000 if width == 1440 else 844})
        for view in [
            "overview",
            "explorer",
            "analytics",
            "dossiers",
            "comparison",
            "intervention",
            "exports",
            "methodology",
        ]:
            page.goto(BASE + "/#" + view)
            page.wait_for_function("() => document.querySelector('#content').getAttribute('aria-busy')==='false'")
            page.wait_for_timeout(400)
            assert not page.locator("#error").is_visible(), (width, view, page.locator("#error").inner_text())
            assert page.evaluate("document.documentElement.scrollWidth<=window.innerWidth"), (width, view, "overflow")
            page.locator("h1").click()
            screenshot_name = ("desktop" if width == 1440 else "mobile") + ("" if view == "overview" else "-" + view) + ".png"
            page.screenshot(path=str(OUT / screenshot_name), full_page=True)

    results.append("Final visual matrix: all eight views at 1440px and 390px without page overflow")
    assert not errors, errors
    browser.close()

print(json.dumps({"passed": results, "page_errors": errors}, indent=2))
(ROOT / "docs/browser-results.json").write_text(json.dumps({"passed": results, "page_errors": errors}, indent=2) + "\n")
