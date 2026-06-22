Ingecart — Brand Guidelines (canonical copy)

Files in this folder:

- `Ingecart_Brand_Guidelines_Source.txt` — original plaintext recommendation (canonical copy).
- `ingecart_brand.css` — lightweight CSS tokens and helpers to apply the visual identity in HTML reports and templates.
- `ingecart_dark_brand.css` — dark theme used for deep strategic reports (black background, white body text, orange accents).

Usage

- To include the brand CSS in an HTML report use:

```html
<link rel="stylesheet" href="../BrandGuidelines/ingecart_brand.css">
```

- Use the logo files in `Informes/ingecart-marketing-kit/Assets/ingecart_assets_v2/` (e.g. `logo ingecart blanco.png`) for headers:

```html
<header class="brand-header">
  <img src="../Assets/ingecart_assets_v2/logo%20ingecart%20blanco.png" class="brand-logo" alt="Ingecart logo">
  <div class="brand-title"><h1>Informe</h1><div class="muted">Subtítulo</div></div>
</header>
```

Deep reports (required behavior)

The project includes a `generate_deep_report.py` script that implements a cascade-style,
multi-channel information gathering process and renders a final deep strategic report.

- The generator must perform:
  - Multi-channel searches (web, local research files, news sources and optionally APIs).
  - Multi-agent/cascade scraping: every discovery may seed more searches until no new sources are found.
  - Consolidation of raw evidence into a local JSON database under `Informes/ingecart-marketing-kit/Data/`.
  - Validation/duplication removal and evidence scoring before producing the final output.
  - Render a final deep HTML report using the dark theme: black background, body text white, headings and accents in Ingecart orange.

Usage example for deep reports:

```bash
python ../Scripts/generate_deep_report.py --company PARA
```

Notes

- The dark theme CSS `ingecart_dark_brand.css` is intentionally minimal — extend with additional tokens as needed.
- The generator is a scaffold for cascade scraping and consolidation; for production-grade crawling and multi-agent orchestration integrate with your favorite tools (Scrapy, Playwright, or a headless agent farm).
- Store sensitive credentials (API keys) outside the repo and inject them at runtime.

