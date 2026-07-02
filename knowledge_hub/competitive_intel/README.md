# Competitive Intelligence (Knowledge Hub) — Scaffold

This folder contains a safe, non-destructive scaffold for the
Competitive Intelligence Engine. It is intentionally conservative and
performs no network crawling, scraping or automatic indexing.

Goals:

- Provide package structure and contracts for the pipeline
- Include a SQLite schema for local development (`schema.sql`)
- Offer indexer/search/graph/score skeletons that are callable but
  do not run automatically
- Provide unit tests using only synthetic data

Usage (development):

1. Review the code under `knowledge_hub/competitive_intel/`.
2. Run unit tests (they are self-contained and use temporary files):

```bash
python -m unittest tests.test_competitive_intel
```

Rules (IMPORTANT):

- This scaffold does NOT perform any scraping or web requests.
- Do NOT call production fetchers from automated CI without review.
- Indexing is explicit: call `Indexer.add_document(...)` yourself.

Next steps when ready:

- Implement concrete fetchers (requests/Playwright) in a separate module
- Add robust parsers (BeautifulSoup, PyMuPDF, Tesseract) behind feature
  flags
- Add entity normalization and a persistent graph store if needed
