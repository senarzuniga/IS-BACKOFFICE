Ingecart — Brand Guidelines (canonical copy)

Files in this folder:

- `Ingecart_Brand_Guidelines_Source.txt` — original plaintext recommendation (canonical copy).
- `ingecart_brand.css` — lightweight CSS tokens and helpers to apply the visual identity in HTML reports and templates.

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

Notes

- The palette tokens in `ingecart_brand.css` are based on the recommendations in `Ingecart_Brand_Guidelines_Source.txt` (black primary, orange accent, white technical, and greys).
- If you need a machine-readable brand JSON, see `informes/ingecart-marketing-kit/Assets/ingecart_assets_v2/ingecart_brand_complete.json`.
- Keep orange accents limited (rule: 70% dark | 20% greys | 10% orange) to maintain visual impact.
