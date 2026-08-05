# ESTESA Technology Comparison Matrix

Date: 2026-07-24

## Matrix 1. Core Technology Trade-off

| Technology domain | Preferred INGECART-oriented option | Alternatives considered | Strengths | Limitations | Recommendation rationale |
|---|---|---|---|---|---|
| Indoor reel positioning | UWB-first RTLS + RFID checkpoints | BLE RSSI, BLE AoA only, vision-only, GPS | High indoor location confidence, robust identity continuity | Higher initial design effort than BLE RSSI-only | Best balance of traceability, resilience, and industrial reliability |
| Reel transport to corrugator | INGETRANS rail-based automated flow | Forklift-only, manual scheduling | Deterministic feed, lower safety exposure, better continuity | Requires layout engineering and commissioning discipline | Strongest improvement in throughput stability and risk reduction |
| Scrap evacuation | SR-1400 continuous engineered system | Local conveyors, manual removal | Continuous flow, sealed chain design, energy efficiency | Plant-specific integration effort | Superior energy and operational cleanliness profile |
| Waste and WIP intralogistics | AMR fleet layer | Fixed conveyors everywhere, forklift routines | Route flexibility, scalable missions, lower manual effort | Payload/autonomy specifics depend on chosen platform | Best for variable routing and phased deployment |
| End-of-line palletizing | Heavy Duty + Plug and Play product split | Manual stacking, low-spec generic cells | High throughput option + rapid deployment option | Heavy Duty exact payload must be validated per project | Portfolio covers both premium and fast-start customer profiles |
| Pre-capex validation | Industrial Digital Twin | Spreadsheet-only planning | Scenario confidence, collision and flow simulation | Model quality depends on input fidelity | Reduces decision risk and strengthens investment case |
| Runtime decision support | AI Engineering Platform | Manual reports, isolated dashboards | Cross-role recommendations, faster diagnostics | Requires clean data governance | Highest leverage for continuous improvement and adoption scale |

## Matrix 2. Product Family Positioning

| Product family | Best-fit plant profile | Main KPI impact | Deployment complexity | Time-to-value profile |
|---|---|---|---|---|
| INGETRANS | Corrugator-centered reel logistics bottlenecks | Throughput stability, safety | Medium-High | Medium |
| SR-1400 | High scrap generation lines | Energy, housekeeping, flow continuity | Medium | Medium |
| AMR Waste/WIP | Dynamic route changes and constrained aisles | Labor reduction, routing flexibility | Medium | Medium-Fast |
| Heavy Duty Palletizer | Multi-out, heavy, high-speed lines | End-of-line cadence and quality | High | Medium |
| Plug and Play Palletizer | Fast automation adoption needs | Fast commissioning and predictable output | Low-Medium | Fast |
| Digital Warehouse + RTLS | Traceability-sensitive operations | Search time, stock accuracy, genealogy | Medium | Medium |
| Digital Twin + AI layer | Strategic modernization programs | Capex confidence and closed-loop optimization | Medium | Medium-Long |
