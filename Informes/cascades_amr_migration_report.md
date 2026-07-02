# Migration from Fixed Transfer Car (BHS) to an AMR Fleet

Prepared for: Cascades — Engineering & Operations

Date: <!-- version placeholder -->

## Cover

Migration from Fixed Transfer Car (BHS) to an AMR Fleet

Key Integration Points and High-Density WIP Layout Design for a Corrugated Packaging Plant

---

## Executive Summary

This document outlines a pragmatic migration strategy from a fixed transfer-car model (BHS) to an Autonomous Mobile Robot (AMR) fleet for a corrugated packaging plant. The proposal focuses on preserving throughput while increasing effective floor density, removing single points of failure, improving routing flexibility and reducing mechanical maintenance through distributed material handling.

The AMR approach decouples material flow from rigid conveyor topology, enabling high-density WIP blocks, JIT feeding of converting lines, and resilient multi-robot redundancy. The recommended next phase is a concept validation and layout engineering package including site survey, throughput simulation and ROI modelling.

---

## Current vs Proposed System (Summary)

| Operational Variable | Current System (BHS Transfer / Belts) | Proposed System (AMR + Trident Stations) | Operational Impact |
|---|---|---|---|
| Space Density | Fixed lanes, large footprint, limited stacking density | Omnidirectional storage, compact blind-block storage, higher volumetric density | Increase usable floor area & reduce plant footprint for WIP |
| Flow Flexibility | Rigid paths and handoffs, single-route bottlenecks | Dynamic routing, multi-path delivery, localized stations | Faster changeovers and less downtime caused by layout changes |
| Mechanical Maintenance | High mechanical exposure (chains, belts, transfer cars) | Lower mechanical wear; robots require scheduled service | Reduced scheduled maintenance; more predictable spares planning |
| Flow Bottlenecks | Transfer car and trident station act as choke points | Distributed pick/drop and parallel trident stations | Better throughput resiliency and less cascading delays |
| Expandability | Large civil works for expansion | Scale by adding AMRs and storage cells | Lower incremental expansion cost |
| Routing Adaptability | Low — requires physical reroute | High — fleet manager reconfigures paths | Quick adaptation to new product mixes |
| Operational Resilience | Single point failures can stop lines | AMR redundancy and rerouting avoid stoppages | Improved uptime and fault tolerance |
| Product Handling Quality | Transfer shock and complex handoffs | Soft-handling, controlled trident interfaces | Fewer board damages and reduced waste |

---

## Key Value Drivers

1. Maximized Floor Space / High-Density WIP
   - Executive: Convert aisle and conveyor volume to compact blind-block storage served by AMRs.
   - Technical: Use zero-clearance stacks and cellized storage; AMRs operate between cells to shuttle full boards.
   - Consequence: Higher working inventory on the same footprint and faster retrieval for JIT feeding.

2. Elimination of Single Point of Failure
   - Executive: Replace the single transfer-car with distributed AMR operations and multiple trident handoff points.
   - Technical: Multi-robot redundancy with fleet-manager rerouting and local buffering.
   - Consequence: Reduced downtime risk and simpler fault-isolation procedures.

3. Decoupled Operational Flows
   - Executive: Decouple corrugator-to-converting flow to enable asynchronous buffering and prioritized feeds.
   - Technical: Trident stations act as local buffers and job-change points; AMR performs prioritized deliveries.
   - Consequence: Smoother line work and higher effective throughput during product changeovers.

4. Reduced Mechanical Maintenance
   - Executive: Move away from heavy fixed machinery towards serviceable robotic units and modular stations.
   - Technical: Predictable maintenance intervals for AMRs; reduced conveyor/transfer car spare parts.
   - Consequence: Lower unplanned maintenance and easier long-term OPEX planning.

5. Improved Board Protection / Waste Reduction
   - Executive: Soft handling, flexible stop/start, and precise pose control reduce board damage.
   - Technical: Controlled trident handoffs with minimal sliding; AMR speed ramping on approach.
   - Consequence: Lower scrap rates and higher first-pass yield.

---

## Layout Blueprint

The HTML deliverable includes an inline SVG schematic representing the corrugator, main trident station, six converting lines, a central dual-lane AMR highway, a high-density WIP block and the shipping area. The diagram is schematic and is intended for concept validation; site dimensions must be verified.

---

## Material Flow Dynamics (4 steps)

1. Inbound induction from corrugator
   - Description: Boards exit the corrugator and are inducted to the main trident buffer.
   - AMR role: Move full pallets/board stacks away from corrugator to deep-lane WIP or local tridents.
   - WCS role: Assign job IDs, create storage addresses, and update expected retrievability.

2. Deep-lane WIP allocation
   - Description: Dense, blind-block storage holds batches prioritized by production horizon.
   - AMR role: Shuttle stock between deep storage and local buffers on demand.
   - WCS role: Balance fill levels to preserve throughput and minimize travel distance.

3. JIT converting line feeding
   - Description: Lines receive sequenced boards via trident stations close to each converting line.
   - AMR role: Deliver boards to tridents with precise timing and orientation.
   - WCS role: Interface with MES/PLCs to anticipate changeovers and pre-stage material.

4. Reverse logistics / overruns handling
   - Description: Overruns or rejects are routed to rework or quarantine zones without blocking the main flow.
   - AMR role: Isolate and transport exceptions to designated cells.
   - WCS role: Flag exceptions and update downstream availability and rework queues.

---

## Engineering & Integration Considerations

- WCS / AMR Fleet Manager coordination: define API and events for job allocation, reservation, and preemption.
- Trident station integration points: electrical/IO handshake, mechanical location references, and safety interlocks.
- Curing / buffering logic: define minimum/maximum residency times and fallback rules for slow-moving items.
- Line demand signals and job-change anticipation: use PLC/MES signals to drive pre-staging and prefetch heuristics.
- Traffic orchestration: dual-lane highway with lane-splitting rules, negotiated passes at handoff points, and deadlock avoidance.
- Exception handling: fallback-to-buffer logic, manual override workflows, and degraded-mode policies.

---

## Recommended Next Step: Concept Validation & Layout Engineering

Proposed work packages:

- Site survey & dimensional validation
- Throughput simulation and bottleneck analysis
- WIP capacity model and blind-block sizing
- AMR fleet sizing and route modeling
- Trident station interface definition and mock-ups
- Phased migration plan and pilot deployment
- ROI / OPEX vs CAPEX modelling and sensitivity analysis

---

## Notes & Assumptions

- This document provides an architectural-level recommendation and does not depend on proprietary machine-level specifications.
- Detailed mechanical and electrical integration will require site-specific surveys and OEM interfaces.
