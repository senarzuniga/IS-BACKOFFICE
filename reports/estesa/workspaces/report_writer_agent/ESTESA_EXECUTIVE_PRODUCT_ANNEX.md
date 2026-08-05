# ESTESA Executive Product Annex

Date: 2026-07-24
Scope: INGECART solutions relevant to corrugated and packaging modernization.

This annex consolidates the technical catalogue of INGECART solutions referenced in the ESTESA Executive Engineering Report. Each sheet focuses on industrial function, engineering logic, integration potential, and available technical references.

## 1. INGETRANS

### Overview
Rail-based reel-feeding and internal transport architecture for corrugated plants, designed to replace unstable forklift-dependent supply with synchronized delivery and return logic.

### Industrial problem solved
Interruptions in corrugator reel supply, excessive forklift circulation, and weak coordination between warehouse and production demand.

### Engineering solution
Automated rail-guided internal logistics linked to warehouse status, exchange zones, and dispatch logic.

### Main functionalities
- Automatic reel delivery and return.
- Exchange and track coordination.
- Integration with warehouse logic.

### Operational benefits
- Less forklift traffic.
- More stable corrugator supply.
- Improved safety and lower manual handling exposure.

### Typical applications
- Corrugator reel rooms.
- Non-automated roll warehouses.

### Integration possibilities
- Digital Warehouse
- RFID / RTLS Positioning
- Industrial Digital Twin
- Full Waste Control

### Related products
- Digital Warehouse
- RFID / GPS / RTLS Positioning
- Industrial Digital Twin

### Available documentation
- `DIGITAL TWIN SIMULATION REPORT BROCHURE.png`
- `INGETRANS FOR OFFERS Techncal DOC.docx`
- `INTRALOGISTICS INGETRANS.txt`
- `ingetrans_DigitalTwin.txt`
- `simulador reel loading V4.txt`

## 2. AMR Intralogistics Waste Management

### Overview
Scalable autonomous intralogistics platform for waste collection and plant-support logistics under coordinated fleet control.

### Industrial problem solved
Manual and fragmented internal logistics around waste, support materials, and repetitive low-value transport tasks interfere with production continuity and create avoidable dependency on operators and forklifts.

### Engineering solution
Mission-based AMR fleet architecture connected to production requirements and capable of serving several internal logistics functions through the same routing and dispatch model.

### Main functionalities
- Automatic waste collection.
- Automatic waste weighing.
- Waste traceability.
- Transport of production support materials.
- Automatic replenishment of palletizer interlayers.
- Transport and positioning of mandrels.
- Transport and positioning of printing cliches.
- Movement of empty pallets where applicable.
- Synchronization with production requirements.
- Interaction with MES.
- Autonomous routing and fleet coordination.
- Modular expansion for additional logistics tasks.

### Operational benefits
- Less manual transport effort.
- Cleaner and more traceable internal flow.
- Better logistics response to changing production priorities.
- Easier expansion toward additional autonomous internal missions.

### Typical applications
- Corrugated plants with changing route priorities.
- Plants where one AMR fleet must support multiple repetitive logistics tasks.
- Staged modernization programs where flexible missions are preferable to fixed-route infrastructure.

### Integration possibilities
- SR-1400
- Full Waste Control
- RFID / RTLS Positioning
- Palletizing systems

### Related products
- AMR Intralogistics WIP Management
- Full Waste Control
- SR-1400

### Available documentation
- `INTRALOGISTICS AMR.pdf`
- `INTRALOGISTICS AMR.pptx`
- `TECHNICAL REPORT AMR INTR.txt`
- `TEXTO OFERTAS AMR CORRUGADORA WAIST MANAGEMENT.docx`

## 3. AMR Intralogistics WIP Management

### Overview
Dispatchable WIP transfer architecture for inter-stage movement, temporary buffers, and staged flow balancing.

### Industrial problem solved
Manual transfer of intermediate loads creates congestion, variable response times, and unstable staging between process steps.

### Engineering solution
Autonomous mission-based transport between stages, buffers, and handoff points.

### Main functionalities
- Dynamic routing.
- Buffer-to-stage transfer.
- Temporary staging support.

### Operational benefits
- Lower congestion.
- Improved stage-to-stage synchronization.
- Reduced dependence on manual transport.

### Typical applications
- Inter-stage transfer.
- Pre-palletizing staging.

### Integration possibilities
- Plug and Play Palletizer
- Heavy Duty Palletizer
- Digital Warehouse

### Related products
- AMR Intralogistics Waste Management
- Full Waste Control

### Available documentation
- `INFORME TÉCNICO AMR WIP.txt`
- `TECHNICAL REPORT AMR INTR.txt`

## 4. Full Waste Control with AMR Intralogistics and Weighing Stations for Reels In and Reels Out

### Overview
Closed-loop material accountability architecture linking reel entry, reel exit, weight, identity, and movement events.

### Industrial problem solved
Weak reconciliation between consumed material, residual material, and route events creates unexplained loss and poor yield visibility.

### Engineering solution
Combined weighing, transport-event, and identity architecture for material reconciliation.

### Main functionalities
- Reel-in and reel-out weighing points.
- Identity continuity.
- Event-linked transport records.

### Operational benefits
- Lower unaccounted material loss.
- Better yield control.
- More defensible operational reporting.

### Typical applications
- Plants with trim-loss uncertainty.
- Auditable material-governance environments.

### Integration possibilities
- Digital Warehouse
- RFID / GPS / RTLS Positioning
- SR-1400
- AMR Intralogistics

### Related products
- AMR Waste Management
- Digital Warehouse
- RFID / GPS / RTLS Positioning

### Available documentation
- `RFID reel management system.pptx`
- `INGECART – RFID PAPER ROLL TRACKING & STATION VALIDATION SOLUTION.docx`
- `Of. 26-05-073V0 (Ingecart) Real Time Warehouse Management.pdf`

## 5. Heavy Duty Palletizer

### Overview
Robotic high-duty palletizing cell for demanding converting lines requiring stable load formation and industrial repeatability.

### Industrial problem solved
Manual or low-spec end-of-line handling cannot maintain stable cadence in demanding converting environments.

### Engineering solution
Robotic palletizing cell with infeed, load-formation logic, and pallet-handling architecture.

### Main functionalities
- Robotic palletizing.
- Load forming.
- High-duty conveyor integration.

### Operational benefits
- Higher end-of-line cadence consistency.
- Lower ergonomic exposure.
- Standardized robotic operation.

### Typical applications
- Multi-out converting lines.
- Heavy load patterns.

### Integration possibilities
- Plug and Play Palletizer family
- AMR WIP systems

### Related products
- Plug and Play Palletizer
- KUKA robotic ecosystem

### Available documentation
- `ING_HEAVYDUTYPALLETIZER®.txt`
- `Automatic Robotic Palletizers .pptx`
- `Custom Automatic Robotic Palletizers.pptx`
- `Palletizer System - 1 min.mp4`

## 6. Plug and Play Palletizer

### Overview
Pre-engineered palletizing cell for rapid deployment, standardized commissioning, and broad bundle-format flexibility.

### Industrial problem solved
Customers need palletizing automation without the integration burden of a fully bespoke robotic project.

### Engineering solution
Standardized palletizing cell with servo-driven gripping and low-overhead deployment model.

### Main functionalities
- 12 bundles/minute stable production.
- 2300 mm pallet height.
- 1200 x 1200 mm area.
- More than 50 bundle formats.

### Operational benefits
- Faster time to production.
- Easier project scoping.
- Format flexibility.

### Typical applications
- Standardized packaging environments.
- Projects with strict commissioning windows.

### Integration possibilities
- AMR WIP Management
- Digital Twin validation
- End-of-line conveyor take-offs

### Related products
- Heavy Duty Palletizer

### Available documentation
- `ING_PLUG&PALLETIZER offer text.txt`
- `COMPACT PALLETIZER&EASYPACK.pptx`
- `Compact Palletizer.mp4`

## 7. SR-1400

### Overview
Continuous engineered scrap evacuation system with sealed-chain logic, variable-speed control, and process-layout integration.

### Industrial problem solved
Scrap accumulation, energy-intensive waste management, and manual intervention degrade line continuity and housekeeping.

### Engineering solution
Plant-specific continuous waste-evacuation architecture with sealed transport logic and regulated flow.

### Main functionalities
- Continuous evacuation.
- Sealed ramp-chain path.
- Variable-speed control.

### Operational benefits
- Lower energy burden.
- Cleaner process environment.
- Less manual waste handling.

### Typical applications
- Conversion and finishing lines.
- Plants with sustained scrap generation.

### Integration possibilities
- AMR Waste Management
- Full Waste Control

### Related products
- AMR Waste Management
- Full Waste Control

### Available documentation
- `SR1400  TECHNICAL DOC.pdf`
- `SISTEMA RETAL 1400   DETALLE TÉCNICO INGLES OFERTAS.docx`
- `Engineered Waste Logistics System.txt`
- `PPT SISTEMA RETAL 1400. ESP.pdf`

## 8. Digital Warehouse

### Overview
Real-time roll governance layer for location, status, and transaction continuity in non-automated stock areas.

### Industrial problem solved
Manual warehouse routines create weak inventory accuracy, search delays, and low confidence in location status.

### Engineering solution
Real-time roll-state and event-governance layer for warehouse operations.

### Main functionalities
- Real-time location visibility.
- Full traceability of movements.
- Exception and search logic.

### Operational benefits
- Better stock accuracy.
- Lower search time.
- Stronger warehouse discipline.

### Typical applications
- Roll warehouses.
- Intermediate stock zones.

### Integration possibilities
- INGETRANS
- RFID / GPS / RTLS Positioning
- Full Waste Control

### Related products
- INGETRANS
- RFID / GPS / RTLS Positioning
- Industrial Digital Twin

### Available documentation
- `Of. 26-05-073V0 (Ingecart) Real Time Warehouse Management.pdf`

## 9. Industrial Digital Twin

### Overview
Simulation-based engineering environment for layout, route, KPI, and capex validation before physical implementation.

### Industrial problem solved
Plants often commit to logistics and automation changes before understanding flow consequences, interface failure modes, and ROI sensitivity.

### Engineering solution
Discrete-event, scenario-driven validation environment for future-state logistics and modernization alternatives.

### Main functionalities
- Scenario comparison.
- KPI generation.
- Route and layout validation.
- Financial and event-engine integration.

### Operational benefits
- Lower decision risk.
- Better capex prioritization.
- Earlier visibility into bottlenecks.

### Typical applications
- Layout redesign.
- Manual versus automated logistics comparison.
- Future-state validation.

### Integration possibilities
- INGETRANS
- Digital Warehouse
- AMR flows
- Palletizing cells

### Related products
- INGETRANS
- Digital Warehouse

### Available documentation
- `00_FIDELITY_FRAMEWORK.md`
- `01_ARCHITECTURE_REPORT.md`
- `deepseek_html_DIGITAL TWIN SIMULATION REPORT.html`
- `DIGITAL TWIN SIMULATION REPORT BROCHURE.png`

## 10. RFID / GPS / RTLS Positioning

### Overview
Hybrid traceability architecture with UWB-first indoor positioning and RFID identity checkpoints for warehouse and station control.

### Industrial problem solved
Without continuous indoor location and identity continuity, warehouse governance and station validation remain slow and error-prone.

### Engineering solution
UWB-first positioning reinforced by RFID checkpoints and event-linked traceability logic.

### Main functionalities
- Indoor positioning.
- Identity continuity.
- Checkpoint validation.
- Event/API integration.

### Operational benefits
- Stronger traceability.
- Lower ambiguity in warehouse search and movement.
- Better governance of roll-related transactions.

### Typical applications
- Roll location in warehouses.
- Station validation.
- Exception handling.

### Integration possibilities
- Digital Warehouse
- INGETRANS
- Full Waste Control

### Related products
- Digital Warehouse
- INGETRANS
- Industrial Digital Twin

### Available documentation
- `RTLS-UWD Documento tecnico_v2.pdf`
- `Sewio_Evaluacion_RTLS.pdf`
- `Eliko_Evaluacion_RTLS.pdf`
- `RFID reel management system.pptx`
- `INGECART – RFID PAPER ROLL TRACKING & STATION VALIDATION SOLUTION.docx`
