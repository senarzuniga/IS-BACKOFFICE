# Machine Trading Intelligence Pipeline - Integration Guide

## Quick Start (How To Activate Now)

### 1) Activate New Sources In Config
The following sources have been added to `config/sources.yaml`:

**Tier 2 (High Priority - Daily/2x Weekly Scraping):**
- exapro_machinery (24h)
- kitmondo_machinery (24h)
- drupa_exhibitors (168h - event cycles)
- supercorrexpo (168h - event cycles)
- sino_corrugated_wepack (168h - event cycles)

**Tier 3 (Normal Priority - Daily/Weekly):**
- fefco_news (168h)
- ccca_news (168h)
- paperage_news (24h)
- tappi_resources (168h)
- packaging_expansion_monitor (96h)

### 2) Cascade Logic
Trigger patterns are defined in `config/machine_trading_cascade.yaml`:
- Expansion signals → lead scoring +25
- Distress signals → assessment opportunity
- Direct buying intent → immediate sales opportunity (+40)
- Trade fair exhibitors → 60-day pre-event outreach window (+30)
- Used equipment listings → competitive benchmarking

### 3) How To Run (Using IS-BACKOFFICE Pipeline)

```python
from backoffice.ingestion.intelligence import build_pipeline

# Build pipeline with new sources automatically loaded
pipeline = build_pipeline(config_file='config/sources.yaml')

# Run ingestion (will use cascade rules from machine_trading_cascade.yaml)
results = pipeline.execute()

# Access machine-trading-specific results
machine_trading_leads = [
    item for item in results.structured_data 
    if 'machine_trading' in item.get('tags', [])
]

# Check action recommendations
priority_opportunities = [
    item for item in results.actions 
    if item.urgency in ['critical', 'high']
]
```

### 4) Daily Workflow Integration

**Monday 09:00 - Intelligence Update**
- Run pipeline: `python -m backoffice.ingestion.intelligence --run-daily`
- Review high-urgency signals from dashboard
- Prioritize top 10 new accounts by lead score

**Tuesday 10:00 - Outreach Activation**
- Export qualified accounts to CRM template
- Launch outreach sequences for Tier A opportunities
- Create meeting prep for trade-fair leads (if within 60-day window)

**Friday 16:00 - Weekly Review**
- Review signal-to-opportunity conversion rate
- Update target account prioritization
- Adjust source frequency if needed (e.g., increase drupa frequency if event is soon)

## Data Flow Diagram

```
Sources (yaml) 
  ↓
Scraper Agents (Tier 1/2/3) 
  ↓
Structured Extraction (LLM + Regex)
  ↓
Machine Trading Cascade Rules
  ↓
Action Recommendations (Sales Ready)
  ↓
Intelligence Outputs (Supabase + Sales Dashboard)
```

## Integration With Sales Pipeline

Every structured result includes:
- `lead_score`: 0-100 (0=monitor, 50-75=nurture, 75+=qualify immediately)
- `recommended_action`: one of [create_account, create_opportunity, event_outreach, competitive_analysis]
- `urgency`: critical|high|normal|low
- `tags`: [used_machinery, buyer_signals, fruit_packing, flexo_folder_gluer, etc.]

This feeds directly into `templates/prospect_pipeline.csv` with auto-scored accounts ready for outreach.

## Expected Output (Weekly)

**Signal Summary:**
- ~8-15 new expansion signals
- ~5-10 distress/asset signals
- ~20-30 buying-intent listings
- Trade fair exhibitor mapping (event-driven)

**Converted to Accounts:**
- ~5-8 new target accounts per week
- ~2-3 immediate sales opportunities
- ~10-15 nurture/long-tail accounts

**Action Volume:**
- ~25-40 outbound touches per week (email + LinkedIn + calls)
- ~3-5 discovery calls scheduled

## Key KPIs To Track

| Metric | Target | Frequency |
|--------|--------|-----------|
| Signals captured/week | 40-60 | Weekly |
| Signal-to-account rate | >40% | Weekly |
| Account-to-opp rate | >25% | Weekly |
| Average days to meeting | <7 | Weekly |
| Trade fair pipeline | 50+ exhibitor contacts/event | Per event |

## Troubleshooting

**No signals captured?**
- Check `is_active: true` for all sources in sources.yaml
- Verify scraper_type is valid (static/dynamic/antibot)
- Check Supabase connection in `backoffice/ingestion/intelligence/`

**False positives in buying intent?**
- Refine trigger patterns in machine_trading_cascade.yaml
- Add negative keywords (e.g., exclude "careers", "contact_us")
- Increase lead score thresholds before routing to sales

**Low trade fair exhibitor match?**
- Verify drupa/SuperCorrExpo exhibitor pages load correctly (dynamic selectors)
- Increase scraping frequency 30 days before event
- Cross-reference with manual exhibitor list

## Contact for Pipeline Questions
See `backoffice/ingestion/intelligence/` module and `api/routes/intelligence_ingestion.py` for technical details.
