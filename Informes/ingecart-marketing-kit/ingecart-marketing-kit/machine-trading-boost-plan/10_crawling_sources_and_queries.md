# 10 - Crawling Sources and Cascade Query Matrix

## Priority Source List (Seed)

## Tier 1 - Buyer/Seller and Machinery Signals
- https://www.directindustry.com
- https://www.exapro.com
- https://www.kitmondo.com
- https://www.machineseeker.com
- https://www.machinio.com
- OEM and competitor pages already in your `config/sources.yaml` (Fosber, BHS, MarquipWardUnited)

## Tier 2 - Industry and Event Signals
- https://www.fefco.org
- https://cccabox.org
- https://www.drupa.com
- https://www.supercorrexpo.org
- https://www.sino-corrugated.com
- https://www.wepack-expo.com

## Tier 3 - News and Macro Signals
- https://www.paperage.com
- Reuters/Bloomberg manufacturing pages already configured in your source set

## Cascade Query Patterns

### Expansion signals
- "new corrugated plant"
- "packaging facility expansion"
- "new converting line"
- "capacity increase corrugated"

### Distress/asset availability signals
- "corrugated plant closure"
- "packaging plant divestment"
- "line shutdown"
- "asset sale packaging machine"

### Buying intent signals
- "seeking used flexo folder gluer"
- "used fruit packing line"
- "retrofit corrugated line"
- "end-of-line automation corrugated"

### Event and networking signals
- "exhibitor list corrugated"
- "packaging trade show exhibitors"
- "corrugated summit attendees"

## Suggested URL Discovery Cascade
From one event page or company page, recursively collect:
1. Exhibitor/company profile links
2. Product category pages
3. News/press pages
4. Contact and location pages
5. Partner/distributor pages

Then extract entities:
- company
- country
- role (buyer/seller/integrator)
- machine type
- demand/supply indication
- urgency signal

## Data Validation Rule
Every high-value opportunity should be validated with:
- one primary signal (explicit demand/supply mention), and
- one contextual signal (investment activity, expansion, or technical fit)

## Immediate Implementation Notes For IS-BACKOFFICE
- Add these sources to ingestion config with tier and scrape frequency
- Use intelligence scoring to prioritize actionable signals
- Auto-create recommended actions for top-scored accounts
