# Machine Trading Intelligence Pipeline - ACTIVATION CHECKLIST

## ✓ What Has Been Configured

### 1) Source Configuration (`config/sources.yaml`)
**Added 12 new sources** focused on machinery, events, and packaging intelligence:

**Machinery Marketplaces (Tier 2, high priority):**
- exapro_machinery (24h refresh)
- kitmondo_machinery (24h refresh)
- machineseeker (48h refresh)
- machinio (48h refresh)

**Industry Associations & Events (Tier 2, event-driven):**
- fefco_news (168h = weekly)
- ccca_news (168h = weekly)
- drupa_exhibitors (168h, event-triggered)
- supercorrexpo (168h, event-triggered)
- sino_corrugated_wepack (168h, event-triggered)

**News & Signals (Tier 3, continuous monitoring):**
- paperage_news (24h refresh)
- tappi_resources (168h = weekly)
- packaging_expansion_monitor (96h refresh)

### 2) Cascade Rules (`config/machine_trading_cascade.yaml`)
**Configured 5 trigger-based workflows:**
- Expansion signals → lead score +25
- Distress/asset signals → assessment opportunity
- Direct buying intent → immediate sales (+40) 
- Trade fair exhibitors → 60-day pre-event outreach (+30)
- Used equipment listings → competitive benchmarking

### 3) Data Schema Extensions (`config/MACHINE_TRADING_SCHEMA.md`)
**Ready-to-deploy SQL** for:
- intelligence_outputs extensions (machine_type, demand_type, buyer_fit_score)
- ingestion_structured_data fields
- actions table enhancements
- **NEW TABLE**: machine_trading_opportunities (full CRM schema)

### 4) Integration Documentation (`INTELLIGENCE_PIPELINE_INTEGRATION.md`)
**Quick-start guide** with:
- How to activate each source
- Daily workflow (Monday → Friday rhythm)
- Expected output volumes
- KPI tracking dashboard
- Troubleshooting guide

### 5) Quick-Start Script (`ingecart_machine_trading_start.py`)
**Executable Python script** with options:
```bash
python ingecart_machine_trading_start.py --test              # verify sources
python ingecart_machine_trading_start.py --run-daily        # scrape everything
python ingecart_machine_trading_start.py --analyze-signals  # top signals
python ingecart_machine_trading_start.py --generate-crm     # export leads
python ingecart_machine_trading_start.py --full-run         # do all above
```

## 📋 Next Steps to Go Live

### Step 1: Deploy Schema (5 min)
```bash
# From IS-BACKOFFICE root
cd db/migrations
# Copy the SQL from config/MACHINE_TRADING_SCHEMA.md into a new migration file
# OR run directly on Supabase:
psql <supabase-connection-string> < machine_trading_schema.sql
```

### Step 2: Test Sources (2 min)
```bash
python ingecart_machine_trading_start.py --test

# Expected output:
# ✓ ACTIVE | exapro_machinery           | Exapro Used Machinery     | Tier tier2
# ✓ ACTIVE | kitmondo_machinery         | Kitmondo Machinery Exchange | Tier tier2
# ... (all 12 sources should show ✓ ACTIVE)
```

### Step 3: Run First Ingestion (5 min)
```bash
python ingecart_machine_trading_start.py --run-daily

# This will:
# - Scrape all 12 sources
# - Apply cascade rules
# - Extract and normalize company data
# - Generate action recommendations
# - Store results in Supabase
```

### Step 4: Review Results (10 min)
```bash
python ingecart_machine_trading_start.py --analyze-signals

# Shows top signals from last 7 days
# Check quality of extracted data
# Verify urgency scoring makes sense
```

### Step 5: Generate CRM Import (2 min)
```bash
python ingecart_machine_trading_start.py --generate-crm

# Creates: ingecart-marketing-kit/machine-trading-boost-plan/
#          templates/crm_import_qualified_leads.csv
# 
# Use this CSV to populate your first target account list
```

### Step 6: Schedule Daily Run
Add to your CI/CD or cron:
```bash
# Daily at 06:00 UTC
0 6 * * * cd /path/to/IS-BACKOFFICE && python ingecart_machine_trading_start.py --run-daily
```

## 🎯 First Week Quick Wins

**Monday 09:00**
- Deploy schema
- Run --test to verify all sources active
- Run --run-daily for initial scrape

**Monday 15:00**
- Run --analyze-signals to see what was captured
- Review top 10 signals for quality
- Check if any urgent buying-intent signals appeared

**Tuesday 10:00**
- Run --generate-crm to export qualified leads
- Import CSV into prospect_pipeline.csv template
- Start outreach to top 20 accounts

**Friday 16:00**
- Review this week's signal volume and quality
- Check conversion rates (signals → accounts → meetings)
- Adjust cascade rule thresholds if needed

## 📊 Expected Week 1 Outcomes

**Signal Volume:**
- ~50-80 signals captured from all sources
- ~15-25 high-fit signals (score >50)
- ~5-8 immediate opportunities (buying intent or distress)
- ~10-15 trade-fair exhibitor contacts

**Converted to Action:**
- 20-30 new target accounts loaded
- 5-8 immediate outreach sequences started
- 2-3 discovery calls scheduled

## 🔄 Continuous Operation (Weekly Cadence)

**Every Monday:**
1. Check dashboard for new high-urgency signals
2. Update target account priority list
3. Launch outreach to Tier A accounts

**Every Tuesday-Wednesday:**
1. Run discovery calls
2. Qualify opportunities
3. Create ROI proposals

**Every Friday:**
1. Review KPIs: signal volume, conversion rates, pipeline health
2. Adjust source frequency if needed (e.g., increase during trade fairs)
3. Plan next week's targets

## ⚡ Speed-to-Revenue Path

```
Day 1: Deploy schema + verify sources
Day 2: First scrape + review signals
Day 3: Generate CRM import + start outreach
Week 1: Discovery calls, qualification
Week 2-4: Proposals, negotiations
Week 4-12: Deal closing and first revenue
```

## 🚨 Emergency / Troubleshooting

**Pipeline not running?**
- Check `is_active: true` in config/sources.yaml
- Verify Supabase connection in backoffice/ingestion/intelligence/client.py
- Run `python ingecart_machine_trading_start.py --test` for diagnostics

**No signals showing?**
- Wait 30+ minutes (first scrape may take time)
- Check that sources are responding (try opening URLs manually)
- Review ingestion logs: `tail -f logs/intelligence_ingestion.log`

**False positives in demand?**
- Refine trigger patterns in machine_trading_cascade.yaml
- Add negative keywords to exclude irrelevant hits
- Increase lead_score threshold before routing to sales

## 📞 Support

- **Schema questions**: See `config/MACHINE_TRADING_SCHEMA.md`
- **Pipeline integration**: See `INTELLIGENCE_PIPELINE_INTEGRATION.md` 
- **Source details**: See `config/sources.yaml` and `config/machine_trading_cascade.yaml`
- **Sales playbook**: See `machine-trading-boost-plan/` folder (04-09 docs)

## ✅ Ready to Launch?

You have everything needed. Recommended sequence:

```bash
# 1. Terminal 1 - Deploy and test
python ingecart_machine_trading_start.py --test

# 2. Terminal 1 - Run initial scrape
python ingecart_machine_trading_start.py --run-daily

# 3. Terminal 1 - Analyze what you got
python ingecart_machine_trading_start.py --analyze-signals

# 4. Terminal 1 - Export to CRM
python ingecart_machine_trading_start.py --generate-crm

# 5. Add to cron (persistent daily runs)
# Edit your crontab and add:
# 0 6 * * * cd /path/to/IS-BACKOFFICE && python ingecart_machine_trading_start.py --run-daily
```

**Total time to first revenue signal: <1 week**

Good luck! The machine is now ready to find buyers. 🚀
