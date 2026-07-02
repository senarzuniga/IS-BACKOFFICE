#!/usr/bin/env python3
"""
UI Validation for IS-BACKOFFICE using Playwright.
Clicks main sidebar items and verifies expected page text appears.
Writes a JSON result summary.
"""
from __future__ import annotations

import json
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "ui_validation_result.json"
URL = "http://localhost:8501"

try:
    from playwright.sync_api import sync_playwright
except Exception as e:
    print(json.dumps({"ok": False, "error": "playwright_import", "detail": str(e)}))
    sys.exit(2)

checks = [
    {"label": "🏠 Command Center", "expect": "Command Center"},
    {"label": "🎨 INGECART ARTWORK", "expect": "INGECART ARTWORK"},
    {"label": "🧾 Facturación ERP", "expect": "Facturación ERP"},
]

results = {"generated_at": datetime.now().isoformat(), "url": URL, "checks": []}

with sync_playwright() as pw:
    try:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(URL, timeout=30000)
        time.sleep(1.0)

        # Accept any cookie banners or initial dialogs if present (best-effort)
        try:
            # close buttons
            for sel in ['button:has-text("Close")', 'button:has-text("Aceptar")', 'button:has-text("OK")']:
                if page.locator(sel).count() > 0:
                    page.locator(sel).first.click()
        except Exception:
            pass

        body_text = page.content()
        results['initial_loaded'] = True if body_text else False

        # Capture a sidebar HTML snippet (best-effort) for debugging locator failures
        try:
            sb = page.locator('[data-testid="stSidebar"]')
            if sb.count() > 0:
                results['sidebar_html_snippet'] = sb.inner_html()[:2000]
            else:
                results['sidebar_html_snippet'] = body_text[:2000]
        except Exception as _e:
            results['sidebar_html_error'] = str(_e)

        for ch in checks:
            entry = {"label": ch['label'], "expect": ch['expect'], "ok": False, "errors": []}
            try:
                # Prefer searching inside the Streamlit sidebar to avoid false matches
                sidebar = page.locator('[data-testid="stSidebar"]')
                clicked = False

                # Try several candidate text forms: emoji+label, ascii-stripped, and the expected text
                candidates = [ch['label'], ''.join(c for c in ch['label'] if ord(c) < 128).strip(), ch['expect']]
                for cand in candidates:
                    if not cand:
                        continue
                    loc = sidebar.get_by_text(cand, exact=False) if sidebar.count() > 0 else page.get_by_text(cand, exact=False)
                    if loc.count() > 0:
                        try:
                            loc.first.click()
                            clicked = True
                            break
                        except Exception:
                            try:
                                # fallback: force a DOM click
                                loc.first.evaluate("el => el.click()")
                                clicked = True
                                break
                            except Exception:
                                pass

                # If still not clicked, fallback to a case-insensitive XPath search inside the sidebar
                if not clicked:
                    expected_lower = ch['expect'].lower()
                    xpath_expr = f".//*[contains(translate(normalize-space(string(.)), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{expected_lower}')]"
                    loc = sidebar.locator(f"xpath={xpath_expr}") if sidebar.count() > 0 else page.locator(f"xpath={xpath_expr}")
                    if loc.count() > 0:
                        try:
                            loc.first.click()
                            clicked = True
                        except Exception:
                            try:
                                loc.first.evaluate("el => el.click()")
                                clicked = True
                            except Exception:
                                pass

                if not clicked:
                    entry['errors'].append(f"Menu label not found: {ch['label']}")
                else:
                    time.sleep(1.2)
                    content = page.content()
                    if ch['expect'] in content or ch['expect'].lower() in content.lower():
                        entry['ok'] = True
                    else:
                        entry['errors'].append('Expected text not found after click')
                        # save a screenshot for debugging
                        path = ROOT / 'tools' / f"ui_check_{ch['expect'].replace(' ', '_')}.png"
                        try:
                            page.screenshot(path=str(path), full_page=True)
                            entry['screenshot'] = str(path)
                        except Exception as e:
                            entry['screenshot_error'] = str(e)
            except Exception as e:
                entry['errors'].append(str(e))
                entry['trace'] = traceback.format_exc()
            results['checks'].append(entry)

        browser.close()
    except Exception as e:
        results['ok'] = False
        results['error'] = str(e)
        results['trace'] = traceback.format_exc()

OUT.write_text(json.dumps(results, indent=2), encoding='utf-8')
print(str(OUT))

# Exit code: 0 if all ok else 2
all_ok = all(c.get('ok') for c in results.get('checks', []))
if not all_ok:
    sys.exit(2)
sys.exit(0)
