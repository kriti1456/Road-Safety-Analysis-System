"""Chromium regressions for failed requests, rapid navigation and accessible states."""

import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
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


checks = []
chrome_bin = get_chrome_executable()

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=chrome_bin, headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 1000}, reduced_motion="reduce")
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))

    page.goto(BASE)
    page.wait_for_selector(".rank-row")

    page.locator("#start").fill("2026-06-30")
    page.locator("#end").fill("2024-07-01")
    page.locator("#filters button[type=submit]").click()
    assert page.locator("#end").evaluate("(e) => !e.validity.valid")

    page.locator("#reset").click()
    page.wait_for_function("() => !document.querySelector('#content').inert")
    checks.append("Inverted dates blocked inline and reset recovers")

    page.route("**/api/analysis?*", lambda r: r.fulfill(status=503, json={"detail": "Temporarily unavailable"}))
    page.locator("#reset").click()
    page.wait_for_selector("#retry-request")
    assert not page.locator("#content").evaluate("(e) => e.inert")

    page.unroute("**/api/analysis?*")
    page.locator("#retry-request").click()
    page.wait_for_function("() => document.querySelector('#error').hidden && !document.querySelector('#content').inert")
    checks.append("API failure preserves interface and Retry recovers")

    page.route("**/api/export/*", lambda r: r.fulfill(status=503, json={"detail": "Export unavailable"}))
    page.locator("#quick-export").click()
    page.wait_for_selector("#error:not([hidden])")
    assert "Export unavailable" in page.locator("#error").inner_text()
    assert page.locator("#quick-export").get_attribute("aria-disabled") is None

    page.unroute("**/api/export/*")
    page.locator("#dismiss-error").click()
    checks.append("Download failure stays in workspace and re-enables download")

    for view in ["dossiers", "comparison", "intervention", "analytics", "overview"]:
        page.locator(f'#nav a[data-route="{view}"]').click(no_wait_after=True)

    page.wait_for_selector(".rank-row")
    page.wait_for_function("() => !document.querySelector('#content').inert")
    assert page.locator("#page-title").inner_text() == "Overview"
    assert not page.locator("#error").is_visible()
    checks.append("Rapid navigation leaves latest route coherent")

    assert page.locator("#live-status").inner_text().startswith("Overview ready")
    assert page.locator("#content").evaluate("(e) => getComputedStyle(e).animationName") == "none"
    assert page.evaluate("Chart.getChart('monthly').options.animation") is False
    checks.append("Reduced motion and screen-reader completion status")

    page.set_viewport_size({"width": 390, "height": 844})
    assert page.locator("#start").evaluate("(e) => getComputedStyle(e).fontSize") == "16px"
    stamp = page.locator(".map-stamp").bounding_box()
    legend = page.locator(".map-legend").bounding_box()
    assert stamp["y"] + stamp["height"] <= legend["y"] + 1
    checks.append("Phone controls avoid input zoom; map attribution and legend do not overlap")

    page.locator("#factors-data").locator("..").locator("summary").click()
    button = page.locator("#factors-data [data-chart-filter]").first
    value = button.get_attribute("data-chart-filter")
    button.focus()
    page.keyboard.press("Enter")
    page.wait_for_function("() => !document.querySelector('#content').inert")
    assert page.locator("#factor").input_value() == value
    checks.append("Keyboard chart data action applies the shared filter")

    assert not errors, errors
    browser.close()

result = {"passed": checks, "page_errors": errors}
outputs_dir = ROOT / "outputs"
outputs_dir.mkdir(parents=True, exist_ok=True)
(outputs_dir / "resilience-results.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
