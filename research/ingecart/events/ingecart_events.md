# Ingecart — Events & Trade Shows

## Overview

This directory stores intelligence about trade shows, fairs, and strategic
events where Ingecart participates or is relevant as a market signal.

---

## Event Register

### FESPA Barcelona 2026

| Field | Value |
|-------|-------|
| **Event** | FESPA Barcelona 2026 |
| **Type** | International Trade Fair |
| **Sector** | Printing, Signage & Visual Communication |
| **Location** | Barcelona, Spain |
| **Date** | September / October 2026 (exact dates TBC) |
| **Exhibitors** | 700+ |
| **Visitors** | 25,000+ from 100+ countries |
| **Ingecart Role** | Exhibitor (stand) |
| **IAR Role** | Technology Partner co-exhibitor (proposed) |
| **Strategic Reference** | IE-IAR-FESPA-2026-001 |

#### FESPA 2026 — Strategic Relevance

FESPA is the world's largest trade fair for wide-format printing, signage,
textile decoration, and visual communication. Ingecart's participation gives
IAR access to the highest concentration of their joint target customers in
a single 3-day window.

**Key audience at FESPA 2026:**
- Owners of print and signage workshops
- Production directors and industrial buyers
- Workflow automation integrators
- Visual communication agencies
- Substrate, ink, and equipment manufacturers/distributors

---

## Event Files

Naming convention: `YYYY_event_name.{md,json}`

---

## Integration with Supabase

Events are synced to the `ingecart_events` Supabase table.
Run `python db/seeders/seed_ingecart.py --source events` to sync.
