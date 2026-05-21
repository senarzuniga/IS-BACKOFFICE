# Machine Trading Intelligence Schema Extensions

## Why This Matters
Your existing intelligence_outputs and actions tables need to track machine-trading-specific fields to enable the cascade workflow and sales pipeline integration.

## Tables To Extend

### 1) intelligence_outputs (add fields)

```sql
ALTER TABLE intelligence_outputs ADD COLUMN IF NOT EXISTS (
  machine_type VARCHAR(100),  -- fruit_packing, flexo_folder_gluer, corrugated_line, palletizer
  demand_type VARCHAR(100),   -- expansion, distress, buying_intent, competitor_intel
  company_country VARCHAR(2),
  company_industry VARCHAR(100),
  urgency_signal VARCHAR(50),  -- high, medium, low
  buyer_fit_score INT,        -- 0-100
  signal_source_id VARCHAR(100), -- reference to sources.yaml id
  has_contact_info BOOLEAN,
  contact_extracted JSON       -- {name, title, email, phone, linkedin}
);

-- Add useful indices
CREATE INDEX idx_machine_type ON intelligence_outputs(machine_type);
CREATE INDEX idx_demand_type ON intelligence_outputs(demand_type);
CREATE INDEX idx_urgency_signal ON intelligence_outputs(urgency_signal);
CREATE INDEX idx_buyer_fit ON intelligence_outputs(buyer_fit_score) WHERE buyer_fit_score > 50;
```

### 2) ingestion_structured_data (add fields)

```sql
ALTER TABLE ingestion_structured_data ADD COLUMN IF NOT EXISTS (
  machine_trading_relevance VARCHAR(50),  -- high, medium, low, none
  extraction_confidence FLOAT,  -- 0.0-1.0
  extraction_fields JSON,  -- actual extracted values
  normalized_company_name VARCHAR(255),
  normalized_location VARCHAR(255),
  decision_maker_title VARCHAR(100),
  estimated_budget_eur INT
);
```

### 3) actions (new fields for machine trading)

```sql
ALTER TABLE actions ADD COLUMN IF NOT EXISTS (
  action_type VARCHAR(100),  -- outbound_email, discovery_call, technical_validation, proposal
  machine_opportunity_id VARCHAR(100),
  sales_stage VARCHAR(50),  -- identified, contacted, qualified, proposed, negotiating, won
  next_action_recommendation VARCHAR(500),
  urgency_level VARCHAR(50),  -- critical, high, normal, low
  assigned_to VARCHAR(100),
  sla_deadline TIMESTAMP,
  attempt_count INT DEFAULT 0
);
```

### 4) NEW TABLE: machine_trading_opportunities

```sql
CREATE TABLE IF NOT EXISTS machine_trading_opportunities (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  
  -- Account Info
  company_name VARCHAR(255) NOT NULL,
  company_country VARCHAR(100),
  company_segment VARCHAR(100),  -- converter, packer, group, integrator
  
  -- Opportunity
  opportunity_type VARCHAR(100),  -- fruit_packing, flexo_folder_gluer, turnkey_relocation
  estimated_value_eur INT,
  timeline_estimate VARCHAR(50),  -- 0-3m, 3-9m, 9m+
  
  -- Decision Makers
  decision_makers JSON,  -- array of {name, title, email, phone}
  
  -- Pipeline
  pipeline_stage VARCHAR(50),  -- identified, contacted, discovered, qualified, proposed, negotiating, won, lost
  pipeline_stage_updated_at TIMESTAMP,
  last_contact_date TIMESTAMP,
  
  -- Scoring
  bant_budget BOOLEAN,
  bant_authority BOOLEAN,
  bant_need BOOLEAN,
  bant_timing BOOLEAN,
  technical_fit_score INT,
  lead_score INT,
  
  -- Sources
  source_signals TEXT[],  -- array of source_ids that contributed to this opp
  intelligence_ref_id UUID REFERENCES intelligence_outputs(id),
  
  -- Notes
  notes TEXT,
  next_action VARCHAR(500),
  assigned_to VARCHAR(100),
  
  UNIQUE(company_name, company_country, opportunity_type)
);

CREATE INDEX idx_opp_pipeline ON machine_trading_opportunities(pipeline_stage);
CREATE INDEX idx_opp_score ON machine_trading_opportunities(lead_score) WHERE pipeline_stage != 'lost';
CREATE INDEX idx_opp_assigned ON machine_trading_opportunities(assigned_to);
```

## Data Flow Example

```
paperage_news scrapes → "XYZ Converters announces €2M expansion in Portugal"
  ↓
Extraction: company="XYZ Converters", country="PT", investment="€2M", signal="expansion"
  ↓
Cascade rule: expansion_signals → lead_score=+25
  ↓
intelligence_outputs INSERT: {company, country, demand_type="expansion", urgency="high"}
  ↓
actions INSERT: {action_type="outbound_email", sla=24h}
  ↓
machine_trading_opportunities INSERT: {company, stage="identified", score=45}
  ↓
Sales team sees in dashboard → starts outreach
```

## Query Examples For Sales Dashboard

```sql
-- Top 20 hottest opportunities this week
SELECT * FROM machine_trading_opportunities 
WHERE pipeline_stage IN ('contacted', 'discovered') 
AND updated_at > NOW() - INTERVAL '7 days'
ORDER BY lead_score DESC
LIMIT 20;

-- All critical-urgency signals awaiting outreach
SELECT * FROM intelligence_outputs 
WHERE urgency_signal = 'high' 
AND machine_type IS NOT NULL
AND created_at > NOW() - INTERVAL '24 hours'
ORDER BY buyer_fit_score DESC;

-- Conversion funnel this month
SELECT 
  pipeline_stage,
  COUNT(*) as count,
  AVG(lead_score) as avg_score
FROM machine_trading_opportunities
WHERE created_at > DATE_TRUNC('month', NOW())
GROUP BY pipeline_stage
ORDER BY count DESC;

-- Assigned work for specific sales owner
SELECT * FROM machine_trading_opportunities 
WHERE assigned_to = 'javier@ingecart.eu'
AND pipeline_stage != 'won'
ORDER BY lead_score DESC, next_action_due ASC;
```

## Realtime Updates (for Supabase RLS)

Enable real-time subscriptions for critical actions:

```sql
ALTER PUBLICATION supabase_realtime ADD TABLE actions;
ALTER PUBLICATION supabase_realtime ADD TABLE machine_trading_opportunities;
ALTER PUBLICATION supabase_realtime ADD TABLE intelligence_outputs;
```

## Migration Script (one-time setup)

Save as `db/migrations/machine_trading_schema.sql` and run:

```bash
# From IS-BACKOFFICE root
python -c "
from db.client import run_migration
run_migration('db/migrations/machine_trading_schema.sql')
"
```

## Backfill Existing Intelligence Data

After schema update, enrich existing intelligence_outputs with machine_trading fields:

```python
from backoffice.ingestion.intelligence.agents import ExtractorAgent

# Re-run extractor on existing data
extractor = ExtractorAgent()
enriched = extractor.enrich_machine_trading_fields(all_existing_outputs)

# Upsert back to Supabase
for item in enriched:
    db.intelligence_outputs.update(item.id, item.machine_trading_fields)
```

## Testing The Schema

```sql
-- Insert test opportunity
INSERT INTO machine_trading_opportunities (
  company_name, company_country, opportunity_type, pipeline_stage, lead_score
) VALUES (
  'Test Converter S.L.', 'ES', 'fruit_packing', 'contacted', 65
);

-- Verify
SELECT * FROM machine_trading_opportunities WHERE company_name LIKE 'Test%';
```

## Maintenance

**Monthly:**
- Archive won/lost opportunities older than 12 months to history table
- Rebuild indices if query performance degrades
- Review stale "identified" opportunities (no contact >30 days)

**Weekly:**
- Purge old false-positive signals
- Update decision_maker contacts from LinkedIn enrichment
