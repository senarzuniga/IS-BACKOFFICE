# Ingecart — Web Scraping & Crawling Data

## Overview

This directory stores raw and processed data collected from public web
sources about Ingecart and the printing/signage sector.

> **Important:** Only public, legally-accessible data is stored here.
> All scraping operations respect `robots.txt` and terms of service.

---

## Data Collection Targets

### Tier 1 — Ingecart Direct
| Target | URL | Data Points | Last Scraped |
|--------|-----|------------|-------------|
| Ingecart website | To be confirmed | Products, services, news, contacts | Pending |
| LinkedIn profile | To be confirmed | Company size, activity, people | Pending |

### Tier 2 — Sector Portals
| Target | URL | Data Points | Last Scraped |
|--------|-----|------------|-------------|
| FESPA exhibitor list | fespa.com | Exhibitors, products, stands | Pending |
| Printing industry news | Various | Trends, competitor activity | Pending |

---

## Collected Data Files

Naming convention: `YYYY-MM-DD_source_descriptor.{json,csv,txt}`

Examples:
- `2026-05-10_ingecart_website_products.json`
- `2026-05-10_fespa2026_exhibitor_list.csv`
- `2026-05-10_linkedin_ingecart_company.json`

---

## Scraping Status

| Source | Status | Notes |
|--------|--------|-------|
| Ingecart website | 🔲 Pending | Requires confirmed URL |
| FESPA exhibitor portal | 🔲 Pending | Available post-registration |
| LinkedIn | 🔲 Pending | API access required |

---

## Instructions for New Scraping Runs

1. Place raw data files in this directory following the naming convention
2. Run `python db/seeders/seed_ingecart.py --source web_scraping` to parse
   and load data into Supabase
3. Commit cleaned data files (not raw HTML dumps)
