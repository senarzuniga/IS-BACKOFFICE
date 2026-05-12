-- =============================================================================
-- Migration 001 — Ingecart Schema
-- IS-BACKOFFICE | Supabase Database
-- =============================================================================
-- Run this migration in your Supabase SQL editor or via the Supabase CLI:
--   supabase db push
-- =============================================================================

-- ---------------------------------------------------------------------------
-- Extensions
-- ---------------------------------------------------------------------------
create extension if not exists "pgcrypto";   -- gen_random_uuid()
create extension if not exists "pg_trgm";    -- fuzzy text search on names

-- ---------------------------------------------------------------------------
-- 1. ingecart_company
--    Singleton-style table: one row per Ingecart entity variant.
--    Stores the canonical company profile for Ingecart.
-- ---------------------------------------------------------------------------
create table if not exists ingecart_company (
    id               uuid primary key default gen_random_uuid(),
    legal_name       text not null,
    trade_name       text not null,
    industry         text,
    sector           text,
    country_primary  text default 'Spain',
    geography        jsonb,          -- { primary, secondary[], reach }
    currency         char(3) default 'EUR',
    languages        text[],
    strengths        text[],
    growth_vectors   text[],
    tech_appetite    jsonb,          -- { areas_of_interest[], readiness_level }
    profile_version  text default '1.0',
    created_at       timestamptz default now(),
    updated_at       timestamptz default now()
);

comment on table ingecart_company is
    'Canonical company profile for Ingecart. Used by IS-BACKOFFICE and '
    'Adaptative-Sales-Engine for lead enrichment and competitive context.';

-- ---------------------------------------------------------------------------
-- 2. ingecart_products
--    Product and equipment catalog items.
-- ---------------------------------------------------------------------------
create table if not exists ingecart_products (
    id                              uuid primary key default gen_random_uuid(),
    product_code                    text unique,            -- e.g. ING-PROD-001
    name                            text not null,
    category                        text,                   -- large_format_printing | cutting_finishing | consumables | workflow_software
    subcategory                     text,
    description                     text,
    vendor                          text,                   -- null = Ingecart own / distributed
    market_segments                 text[],
    currency                        char(3) default 'EUR',
    unit_price_eur                  numeric(12,2),
    technology_integration_candidate boolean default false,
    ai_agent_fit                    text,                   -- production_optimisation | intelligent_pricing | predictive_maintenance
    lifecycle_stage                 text default 'active',  -- active | discontinuing | new
    created_at                      timestamptz default now(),
    updated_at                      timestamptz default now()
);

comment on table ingecart_products is
    'Ingecart product and equipment catalog. Consumed by Adaptative-Sales-Engine '
    'for pricing signals and solution matching.';

-- ---------------------------------------------------------------------------
-- 3. ingecart_contacts
--    Key people at Ingecart (management, commercial, technical).
-- ---------------------------------------------------------------------------
create table if not exists ingecart_contacts (
    id            uuid primary key default gen_random_uuid(),
    full_name     text,
    role          text,
    department    text,
    email         text,
    phone         text,
    linkedin_url  text,
    notes         text,
    source        text,             -- how the contact was obtained
    verified      boolean default false,
    created_at    timestamptz default now(),
    updated_at    timestamptz default now()
);

comment on table ingecart_contacts is
    'CRM-grade contact register for Ingecart stakeholders.';

-- ---------------------------------------------------------------------------
-- 4. ingecart_documents
--    All documents associated with Ingecart: reports, contracts,
--    marketing materials, research summaries, pitch decks, case studies.
-- ---------------------------------------------------------------------------
create table if not exists ingecart_documents (
    id              uuid primary key default gen_random_uuid(),
    title           text not null,
    category        text not null,  -- report | contract | marketing_kit | pitch_deck | case_study | roi_calculator | research | web_scraping | other
    subcategory     text,
    file_path       text,           -- relative path in repository
    filename        text,
    source_type     text,           -- txt | pdf | md | json | csv | docx | xlsx
    language        text default 'es',
    raw_text        text,
    summary         text,
    tags            text[],
    client_ref      text default 'ingecart',
    reference_code  text,           -- e.g. IE-IAR-FESPA-2026-001
    document_date   date,
    word_count      int,
    checksum        text,           -- SHA-256
    created_at      timestamptz default now(),
    updated_at      timestamptz default now()
);

comment on table ingecart_documents is
    'All Ingecart-related documents indexed by IS-BACKOFFICE. '
    'Consumed by Adaptative-Sales-Engine for knowledge retrieval.';

-- Full-text search index on title + summary
create index if not exists idx_ingecart_documents_fts
    on ingecart_documents
    using gin(to_tsvector('spanish', coalesce(title,'') || ' ' || coalesce(summary,'')));

-- Trigram index for partial-match search on title
create index if not exists idx_ingecart_documents_title_trgm
    on ingecart_documents
    using gin(title gin_trgm_ops);

-- ---------------------------------------------------------------------------
-- 5. ingecart_research_entries
--    Structured research records: market data, sector studies, web-crawling
--    results, competitive intelligence items.
-- ---------------------------------------------------------------------------
create table if not exists ingecart_research_entries (
    id              uuid primary key default gen_random_uuid(),
    entry_type      text not null,  -- market_data | sector_study | web_scraping | competitive_intel | trend
    title           text not null,
    source          text,           -- URL, publication name, internal reference
    source_date     date,
    content         text,
    structured_data jsonb,
    tags            text[],
    relevance_score numeric(3,2),   -- 0.00 to 1.00
    verified        boolean default false,
    created_at      timestamptz default now(),
    updated_at      timestamptz default now()
);

comment on table ingecart_research_entries is
    'Structured research and intelligence entries about Ingecart and its sector. '
    'Consumed by Adaptative-Sales-Engine for context enrichment.';

-- ---------------------------------------------------------------------------
-- 6. ingecart_events
--    Trade shows, fairs, and strategic events relevant to Ingecart.
-- ---------------------------------------------------------------------------
create table if not exists ingecart_events (
    id                uuid primary key default gen_random_uuid(),
    event_code        text unique,   -- e.g. EVT-FESPA-2026
    name              text not null,
    event_type        text,          -- international_trade_fair | industry_conference | product_launch | other
    sector            text,
    location_city     text,
    location_country  text,
    event_year        int,
    event_date_start  date,
    event_date_end    date,
    date_notes        text,
    scale             jsonb,         -- { exhibitors_estimate, visitors_estimate, countries_represented }
    ingecart_role     text,          -- exhibitor | visitor | sponsor | none
    iar_role          text,          -- technology_partner | visitor | speaker | none
    strategic_report  text,          -- reference to ingecart_documents.reference_code
    audience_segments text[],
    dominant_trends   text[],
    iar_demo_pillars  text[],
    created_at        timestamptz default now(),
    updated_at        timestamptz default now()
);

comment on table ingecart_events is
    'Trade shows and events where Ingecart participates, relevant for IAR '
    'partnership strategy and sales event triggers.';

-- ---------------------------------------------------------------------------
-- 7. ingecart_market_intelligence
--    Aggregated market and competitive intelligence snapshots.
-- ---------------------------------------------------------------------------
create table if not exists ingecart_market_intelligence (
    id              uuid primary key default gen_random_uuid(),
    snapshot_date   date not null default current_date,
    sector          text not null,
    period          text,           -- e.g. "2024-2026"
    key_metrics     jsonb,
    trends          jsonb,          -- array of trend objects
    competitive_landscape jsonb,    -- array of competitor category objects
    target_segments jsonb,          -- array of segment objects
    financial_model jsonb,          -- scenario-based financials
    source_refs     text[],
    created_at      timestamptz default now(),
    updated_at      timestamptz default now()
);

comment on table ingecart_market_intelligence is
    'Aggregated market intelligence snapshots for the printing & signage sector, '
    'scoped to Ingecart context. Used by Adaptative-Sales-Engine for enrichment.';

-- ---------------------------------------------------------------------------
-- Row Level Security (RLS) — enable but keep permissive for service role
-- ---------------------------------------------------------------------------
alter table ingecart_company              enable row level security;
alter table ingecart_products             enable row level security;
alter table ingecart_contacts             enable row level security;
alter table ingecart_documents            enable row level security;
alter table ingecart_research_entries     enable row level security;
alter table ingecart_events               enable row level security;
alter table ingecart_market_intelligence  enable row level security;

-- Allow full access for the service role (server-side operations)
do $$
declare
    t text;
begin
    foreach t in array array[
        'ingecart_company',
        'ingecart_products',
        'ingecart_contacts',
        'ingecart_documents',
        'ingecart_research_entries',
        'ingecart_events',
        'ingecart_market_intelligence'
    ]
    loop
        execute format(
            'create policy if not exists "service_role_full_access" on %I '
            'for all to service_role using (true) with check (true)',
            t
        );
    end loop;
end $$;

-- Allow authenticated users read access (adjust as needed for your auth model)
do $$
declare
    t text;
begin
    foreach t in array array[
        'ingecart_company',
        'ingecart_products',
        'ingecart_documents',
        'ingecart_research_entries',
        'ingecart_events',
        'ingecart_market_intelligence'
    ]
    loop
        execute format(
            'create policy if not exists "authenticated_read" on %I '
            'for select to authenticated using (true)',
            t
        );
    end loop;
end $$;

-- =============================================================================
-- End of migration 001
-- =============================================================================
