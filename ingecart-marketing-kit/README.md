# Ingecart — Marketing Kit

This directory contains all marketing and sales enablement materials related
to Ingecart, intended for use in the IAR × Ingecart strategic collaboration
and for reference by downstream systems like **Adaptative-Sales-Engine**.

---

## Directory Structure

```
ingecart-marketing-kit/
├── pitch_decks/              # Presentation materials for FESPA and partner meetings
├── product_catalog/          # Formatted product and solution sheets
├── brand_assets/             # Logos, colour palette, typography guidelines
├── case_studies/             # Customer success stories and ROI evidence
└── roi_calculators/          # Excel/JSON models for ROI calculation
```

---

## Key Materials

### Pitch Decks
- `ingecart_iar_fespa2026_pitch.md` — Talking points for the IAR × Ingecart
  joint stand at FESPA Barcelona 2026.

### Product Catalog
- See `research/ingecart/products/` for structured product data.
- PDF-ready catalog to be produced from the structured JSON.

### ROI Calculators
- `ingecart_ai_roi_calculator.md` — ROI model for Ingecart customers
  adopting IAR AI agents.

---

## Usage by Adaptative-Sales-Engine

Adaptative-Sales-Engine can consume this kit for:
1. **Lead enrichment** — product knowledge to personalise proposals
2. **Pricing signals** — benchmark pricing from product catalog
3. **Competitive framing** — market intelligence for objection handling
4. **Event triggers** — FESPA participation as a sales signal

Query the Supabase `ingecart_documents` table with
`category = 'marketing_kit'` to retrieve indexed versions of these assets.
