# Ingecart — Research & Intelligence Repository

This directory contains all structured research, intelligence, and data assets
collected about **Ingecart** for use by IS-BACKOFFICE and downstream systems
such as **Adaptative-Sales-Engine**.

---

## Directory Structure

```
research/ingecart/
├── company_profile/          # Core company facts, history, positioning
├── products/                 # Product and equipment catalog data
├── market_intelligence/      # Competitive analysis, sector reports, trends
├── web_scraping/             # Raw and cleaned web-scraping / crawling data
├── contacts/                 # Key people, organisational chart
└── events/                   # Trade shows, fairs, and strategic events
```

---

## Data Sources

| Type | Description |
|------|-------------|
| Executive Reports | Internal IS-BACKOFFICE strategic analyses (see also `informes/`) |
| Web Scraping | Crawled data from Ingecart website and industry portals |
| Sector Studies | Third-party market research on printing & signage industry |
| Event Intelligence | FESPA 2026 and other trade fair analyses |
| Contact Records | CRM-grade contact sheets for Ingecart stakeholders |

---

## Supabase Storage

All structured data in this directory is mirrored to Supabase tables.
Run the seeder to load / refresh the data:

```bash
python db/seeders/seed_ingecart.py
```

Required environment variables:
```
SUPABASE_URL=https://<project>.supabase.co
SUPABASE_SERVICE_ROLE_KEY=<service_role_key>
```

---

## Consumer Systems

- **IS-BACKOFFICE**: ingests all files via `FolderScanner` and `GraphStore`
- **Adaptative-Sales-Engine**: queries Supabase tables for lead enrichment,
  pricing signals, and competitive context
