# IS-BACKOFFICE — Database Layer (Supabase)

This directory contains the Supabase integration for IS-BACKOFFICE:
schema migrations, data seeders, and the client module.

---

## Setup

### 1. Configure environment variables

```bash
cp .env.example .env
# Edit .env and fill in SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY
```

### 2. Run the migration

Open your **Supabase project → SQL Editor** and run the contents of:

```
db/migrations/001_ingecart_schema.sql
```

Or, if using the Supabase CLI:

```bash
supabase db push
```

### 3. Seed Ingecart data

```bash
# Seed all Ingecart data sources
python db/seeders/seed_ingecart.py

# Seed a specific source
python db/seeders/seed_ingecart.py --source company
python db/seeders/seed_ingecart.py --source products
python db/seeders/seed_ingecart.py --source events
python db/seeders/seed_ingecart.py --source documents
python db/seeders/seed_ingecart.py --source market_intelligence

# Preview without writing (dry run)
python db/seeders/seed_ingecart.py --dry-run
```

---

## Directory Structure

```
db/
├── client.py               # Supabase client singleton (reads env vars)
├── migrations/
│   └── 001_ingecart_schema.sql   # Ingecart tables + RLS policies
└── seeders/
    └── seed_ingecart.py    # Loads all Ingecart data into Supabase
```

---

## Supabase Tables (Ingecart Schema)

| Table | Description |
|-------|-------------|
| `ingecart_company` | Canonical company profile |
| `ingecart_products` | Product and equipment catalog |
| `ingecart_contacts` | Key stakeholder contacts |
| `ingecart_documents` | All indexed documents (reports, marketing, research) |
| `ingecart_research_entries` | Structured research and intelligence records |
| `ingecart_events` | Trade shows and strategic events |
| `ingecart_market_intelligence` | Aggregated market intelligence snapshots |

---

## Consumer Systems

| System | How it Uses Supabase |
|--------|---------------------|
| **IS-BACKOFFICE** | Reads/writes all tables for commercial intelligence ops |
| **Adaptative-Sales-Engine** | Queries `ingecart_documents`, `ingecart_market_intelligence`, `ingecart_products` for lead enrichment |
