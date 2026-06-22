# 07 - Scraping Cascade Plan (Market and Commercial Intelligence)

## Objective
Build a recurring intelligence loop that converts public signals into prioritized sales actions for Ingecart machine trading.

## 1) Cascade Logic (from one signal to many leads)

### Trigger examples
- Plant expansion announcement
- New converting line investment
- Plant closure/divestment news
- Trade show exhibitor announcement

### Cascade flow
1. Capture trigger source (news/site/event)
2. Identify company and plant geography
3. Enrich with decision-makers and likely need type
4. Score account and create action in CRM
5. Launch outreach sequence in <72h

## 2) Source Tiers For Scraping

### Tier 1 (daily/2x week)
- OEM and direct competitor sites
- Active machinery marketplaces
- Top trade media with expansion/closure signals

### Tier 2 (weekly)
- Association updates (FEFCO, CCCA, related bodies)
- Event websites (drupa, SuperCorrExpo, SinoCorrugated/WEPACK)

### Tier 3 (biweekly/monthly)
- Regulatory and sustainability changes impacting capex decisions
- Broader manufacturing/packaging macro news

## 3) Suggested Extraction Fields
- source_name
- url
- publication_date
- company_name
- location
- event_type (expansion/closure/investment/new product/event)
- machine_category (fruit packing / FFG / corrugated line / end-of-line)
- urgency_signal (high/medium/low)
- inferred_need
- recommended_next_action

## 4) Action Mapping Rules
- High urgency + high fit -> outbound in 24h
- Medium urgency + high fit -> nurture + technical content in 72h
- Low urgency -> monitor list, monthly check

## 5) Integration With Existing IS-BACKOFFICE Pipeline
Use existing intelligence ingestion architecture (`config/sources.yaml` + intelligence route stack) to:
- Add packaging machinery and event sources
- Normalize entities (company, region, machine type)
- Generate action recommendations automatically

## 6) Weekly Intelligence Sprint (90 minutes)
1. Review new scraped signals
2. Confirm top 15 target accounts
3. Assign outreach actions and owners
4. Review conversion from signal -> meeting -> opportunity

## 7) Data Quality Rules
- Never act on one source only for major assumptions
- Validate high-value opportunities with at least 2 independent signals
- Track confidence score per intelligence item

## 8) KPI For Intelligence Engine
- Signals captured/week
- Qualified signals (% of total)
- Signal-to-meeting conversion
- Signal-to-opportunity conversion
- Revenue influenced by intelligence-originated deals
