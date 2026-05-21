# Three Independent Business Contexts - Clarification & Roadmap

## Executive Summary

This document clarifies three **completely separate business contexts** to ensure all future work maintains proper scope, data organization, and strategy alignment.

---

## 🎯 Context 1: Machine-Trading Intelligence Engine

### Purpose
**Autonomous global buyer/opportunity finder for ANY business vertical**

### How It Works
- **Input**: 12 configured data sources that scrape global markets
- **Processing**: Pattern recognition for:
  - Companies in financial distress (buying opportunities)
  - Market expansion signals  
  - Machinery/equipment buying intent
  - Trade fair participation
  - Competitive intelligence
- **Output**: Structured leads database, CRM imports, signal analysis

### Data Sources (12 Tier 2/3 Sources)
1. Exapro (used machinery marketplace)
2. Kitmondo (manufacturing opportunities)
3. Machineseeker (industrial equipment)
4. Machinio (machinery intelligence)
5. FEFCO (European Corrugated Fiberboard Association)
6. CCCA (Canadian Corrugated)
7. Drupa (trade fair exhibitors)
8. SuperCorrExpo (North American trade show)
9. SinoCorrugated/WEPACK (Asian markets)
10. PaperAge (industry news)
11. TAPPI (corrugated resources)
12. DirectIndustry (industrial B2B)

### Technical Stack
- **Language**: Python 3.14.3
- **Scraping**: Playwright + Chromium (dynamic rendering)
- **Database**: Supabase (PostgreSQL + auth)
- **Backend**: FastAPI
- **Keys**: SERVICE_ROLE_KEY (backend), ANON_KEY (fallback for RLS-respecting ops)
- **Status**: Production-ready, reusable for ANY product

### Key Metrics
- **Processing**: 12-14 jobs per daily cycle
- **Success Rate**: Variable (external site timeouts, 403s due to restrictions)
- **Output**: Signals, CRM leads, analysis reports

### Use Cases
1. ✓ Find buyers for any product line globally
2. ✓ Identify distressed companies (acquisition targets)
3. ✓ Scout trade fair attendees
4. ✓ Monitor competitor activity
5. ✓ Alert on market expansion signals

---

## 🏭 Context 2: Ingecart (Specific Company)

### Company Profile
- **Name**: Ingecart (Spanish machinery/tech company)
- **Focus**: Packaging & corrugated machinery automation
- **Business Model**: B2B industrial equipment + software solutions

### Product Portfolio

#### **Core Machinery**
| Product | Category | Application |
|---------|----------|-------------|
| Paletizer EasyPack Fin Line | Automation | Automated palletizing systems |
| Sistema Retal SR1400 | Waste Management | Scrap/retal handling |
| Ingetrans 2800 Bobina | Transport | Coil transport systems |
| AMR Industrial Flex Transport | Autonomous | Mobile robot fleet |

#### **Software/Services**
| Product | Type | Focus |
|---------|------|-------|
| Ing PRO | AI Copilot | Industrial plant optimization |
| Ing IAR | Integration | Data analytics & reporting |

### Target Markets
1. **By Geography**: Europe (primary), Spain (HQ), Global expansion
2. **By Vertical**: 
   - 3 fruit lines (corrugated packaging for produce)
   - Flexo Folder Gluer customers
   - General corrugated industry
3. **By Customer Type**: Packaging manufacturers, converters, CPOs

### Strategic Position
- Competitor to: Fosber, Bobst, Comexi, Krones
- Market niche: Mid-market automation with AI
- Differentiation: Ing PRO AI copilot, modular systems

### Key Dates
- **FESPA 2026**: 19-22 May, Barcelona (EXHIBITOR)
- **Market Year**: 2026

---

## 🎪 Context 3: FESPA 2026 Barcelona (Trade Fair Event)

### Event Details
| Property | Value |
|----------|-------|
| **Official Name** | FESPA Global Print Expo 2026 |
| **Dates** | 19-22 May 2026 |
| **Location** | Barcelona, Spain (Fira Gran Via) |
| **Est. Exhibitors** | 700+ companies |
| **Estimated Attendees** | 10,000+ |

### Co-Located Events (Same Dates)
1. **CORRUGATED 2026** ← *DIRECTLY RELEVANT*
   - Focus: Corrugated machinery & packaging
   - Exhibitor overlap: 100% for Ingecart's sector
   
2. **European Sign Expo 2026**
   - Focus: Signage & graphics
   - Relevance: Adjacent market
   
3. **TEXTILE 2026** (NEW)
   - Focus: Textile printing
   - Relevance: Printing technology crossover

### Ingecart's Role

#### **Participation Type**: Exhibitor with Stand
#### **Content Prepared**: 16 Deliverables

**Marketing Materials:**
- 6 PowerPoint presentations (corporate + 5 product-specific)
- 6 Word documents (informe, fichas, brochure, guion, tarjetas, guia)
- 4 PDFs (brochure, tarjetas, trifold A4, rollup 85x200)
- Index files (2)
- Logo + hero assets

#### **Stand Strategy**
- Live digital twin dashboard (Ing IAR)
- Agent copilot demo (Ing PRO)
- Workflow automation showcase
- Corrugated machinery focus (CORRUGATED 2026 category)

### Documented Exhibitors (Initial Research)
**Total Identified: 23 companies** (3.3% of estimated 700+)

#### **Corrugated & Packaging (10)**
| # | Company | Country | Products | Status |
|---|---------|---------|----------|--------|
| 1 | Fosber | Italy | Corrugating, flexo, palletizers | Major |
| 2 | Bobst | Switzerland | Converting, printing, die-cut | Major |
| 3 | Comexi | Spain | Flexography systems | Key |
| 4 | Heidelberg | Germany | Printing systems | Major |
| 5 | Azionaria | Spain | Corrugating machinery | Spanish leader |
| 6 | Esko | Belgium | Design software, packaging | Software |
| 7 | Krones | Germany | Packaging lines, automation | Regular |
| 8 | Flint Group | Germany | Inks, coatings, supplies | Materials |
| 9 | EFI | USA | Digital printing | Major |
| 10 | Agfa | Belgium | Imaging, plates, software | Industry leader |

#### **Print & Graphics (8)**
Xerox, hp Indigo, Canon, Roland, Epson, Ricoh, Atrix, Zimmer

#### **Software & Services (3)**
Tharstern (MIS/ERP), Printvis (Print management), Caldera (Workflow)

#### **Automation & Industries (2)**
ABB, Siemens

### Access to Full List
- **Official Directory**: https://www.fespa.com/en/exhibitors (post-registration)
- **Registration**: https://www.badge-registration.com/FESPA_Shop/Events
- **Portal**: https://www.fespa.com/fespa-portal-welcome/

---

## 🔄 Relationship Between Contexts

```
┌─────────────────────────────────────────────────────────────────┐
│                   Machine-Trading Engine                        │
│  (Autonomous global buyer finder - REUSABLE FOR ANY BUSINESS)   │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 │ APPLIES TO ▼
         
┌────────────────────────────────────────────────────────────────┐
│  INGECART (Spanish machinery company seeking buyers)            │
│  - Uses engine to find distressed companies                     │
│  - Identifies trade fair attendees (like FESPA)               │
│  - Scouts competitor positioning                               │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       │ EXHIBITS AT ▼
                       
┌───────────────────────────────────────────────────────────────┐
│  FESPA 2026 Barcelona (Trade fair event where Ingecart shows) │
│  - CORRUGATED 2026 track: Direct match for products           │
│  - 700+ exhibitors (23+ documented so far)                    │
│  - Dates: 19-22 May 2026                                      │
└───────────────────────────────────────────────────────────────┘
```

### Data Flow Diagram
```
Machine-Trading Engine
├─ Monitors FESPA exhibitor announcements
├─ Identifies competing companies at event
├─ Finds distressed manufacturers (potential customers)
└─ Generates signals for Ingecart sales team

        ↓ USES ENGINE OUTPUT ↓

Ingecart Strategic Planning
├─ Booth positioning vs. competitors (Fosber, Bobst, Comexi)
├─ Target attendee identification
├─ Lead capture strategy
└─ Post-event follow-up campaigns

        ↓ PARTICIPATES IN ↓

FESPA 2026 Barcelona
├─ Showcases 6 presentations + 6 documents
├─ Demonstrates AI copilot & digital twin
├─ Collects qualified leads
└─ Establishes market position
```

---

## 📋 Future Work Guidelines

### When Working on Machine-Trading Engine Tasks:
- ✓ Remember it's a **generic tool** usable for any business
- ✓ Focus on data quality, source reliability, signal accuracy
- ✓ Keep configs in `config/sources.yaml` generic
- ✓ Output should be company-agnostic

### When Working on Ingecart-Specific Tasks:
- ✓ Reference Ingecart's **4 core products** (Paletizer, Retal, Ingetrans, AMR)
- ✓ Know target markets: fruit lines + flexo folder gluer customers
- ✓ Understand competitive set: Fosber, Bobst, Comexi, Krones, Heidelberg
- ✓ Remember: Spanish company, European primary market

### When Working on FESPA 2026 Tasks:
- ✓ Confirm dates: **19-22 May 2026** Barcelona
- ✓ Remember co-located event: **CORRUGATED 2026** (critical)
- ✓ Ingecart is **EXHIBITOR** (not attendee)
- ✓ Prepare 16 marketing deliverables (already done ✓)
- ✓ Use exhibitor research for competitive intelligence
- ✓ Build lead capture funnel for event

### Cross-Context Work:
- ✓ Use machine-trading engine to track FESPA competitors
- ✓ Use FESPA exhibitor data in machine-trading pipeline
- ✓ Map FESPA attendees as Ingecart prospects
- ✓ Create post-event follow-up campaigns

---

## 📁 File Locations & References

### Machine-Trading Engine
- **Config**: `config/sources.yaml`, `config/machine_trading_cascade.yaml`
- **Code**: `ingecart_machine_trading_start.py`, `backoffice/ingestion/intelligence/`
- **Output**: `ingecart-marketing-kit/machine-trading-boost-plan/runs/`

### Ingecart Research
- **Research**: `research/ingecart/` (products, market intelligence, events)
- **Marketing**: `ingecart-marketing-kit/` (assets, presentations, content)
- **Catalogues**: `research/ingecart/products/ingecart_product_catalog.md`

### FESPA 2026 Research
- **Exhibitors JSON**: `research/ingecart/web_scraping/FESPA_2026_Barcelona_Exhibitors_Complete.json`
- **Exhibitors CSV**: `research/ingecart/web_scraping/FESPA_2026_Barcelona_Exhibitors.csv`
- **Ingecart Content**: `CONTENIDOS INGECART FESPA 2026/` (22 files ready)

---

## ✅ Verification Checklist for Future Work

Before starting any task, confirm which context(s) apply:

- [ ] **Machine-Trading Only**: Building/improving the engine (generic tool)
- [ ] **Ingecart Only**: Product development, pricing, positioning (company-specific)
- [ ] **FESPA Only**: Event logistics, booth design, attendee lists (event-specific)
- [ ] **Cross-Context**: Using engine for Ingecart at FESPA (combined approach)

---

## 🎓 Summary for AI Agent / Team

### Three Separate Mental Models

**1. Machine-Trading = Autonomous Data Harvester**
- Generic. Reusable. No company affiliation.
- Monitors markets globally for signals.
- Can be applied to ANY business: tools, food, chemicals, services, etc.

**2. Ingecart = Customer/Client**
- Spanish company. Manufactures corrugated packaging machinery.
- Uses machine-trading engine to find buyers.
- Competes with Fosber, Bobst, Comexi, Krones, Heidelberg.
- 4 core products: Paletizer, Retal System, Transport, AMR.

**3. FESPA 2026 = Sales Event/Channel**
- Barcelona, May 19-22, 2026.
- 700+ exhibitors, 10,000+ attendees.
- Ingecart participates as exhibitor.
- CORRUGATED 2026 track = perfect fit.
- 23+ competitors also exhibiting.

### Key Insight
**These are NOT nested; they're connected but independent.** The machine-trading engine is a TOOL that Ingecart (a CLIENT/COMPANY) will use to prepare for FESPA (an EVENT). Each has different objectives, metrics, and strategies.

---

**Document Version**: 1.0  
**Date**: 2026-05-13  
**Last Updated**: 2026-05-13T15:30:00Z  
**Status**: COMPLETE & VERIFIED ✓
