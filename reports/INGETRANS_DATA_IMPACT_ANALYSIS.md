# INGETRANS Data Impact Analysis

No validated old/new Sterner delta exists. `Update Required` therefore means migration after source recovery, not permission to substitute a benchmark.

| Parameter | Old Value | New Value | Source | Affected Module | Affected Calculation | Expected Impact | Update Required | Validation Required | Status |
|---|---:|---:|---|---|---|---|---|---|---|
| cycle_time | 30 s | BLOCKED | generic YAML | config_ingetrans.yaml | throughput | unknown | yes | source/page/table | F / REVIEW |
| cycle_time | 45 s | BLOCKED | generic YAML | config_transfer.yaml | transfer capacity | unknown | yes | source/page/table | F / REVIEW |
| transfer_speed | 59 m/min | BLOCKED | hard-coded fallback | core/Reel_load_simulator.py | travel time | unknown | yes | simulator regression | D / REVIEW |
| transfer_speed | 80 m/min | BLOCKED | hard-coded fallback | core/ingetrans_simulation_engine.py; corrugator_engine.py | travel time/utilisation | unknown | yes | simulator regression | D / REVIEW |
| transfer_speed | 80 m/min | BLOCKED | UI default | bobina_load_simulator.py; reel_load_simulator_fixed.py | travel time | unknown | yes | UI + engine | D / REVIEW |
| pickup_time | 6 s | BLOCKED | assumption | engine, pages, demos | handling/mission time | unknown | yes | event timing | E / REVIEW |
| unloading_time | 6 s | BLOCKED | assumption | engine, pages, demos | handling/mission time | unknown | yes | event timing | E / REVIEW |
| corrugator_speed | 220 m/min | BLOCKED | typical-plant benchmark | ingetrans_DigitalTwin.html | consumption/production | unknown | conditional | report regeneration | F / REVIEW |
| reel_consumption | 5.5 reel/h | BLOCKED | typical-plant benchmark | ingetrans_DigitalTwin.html | missions/capacity | unknown | conditional | report regeneration | F / REVIEW |
| reel_weight | 2100 kg | BLOCKED | typical-plant benchmark | ingetrans_DigitalTwin.html | reel life/consumption | unknown | conditional | report regeneration | F / REVIEW |
| delivery_time | 52 s | BLOCKED | published result | ingetrans_DigitalTwin.html | logistics KPIs | unknown | yes | reproduce run | E / REVIEW |
| utilisation | 68% | BLOCKED | commercial calibration | core/commercial_simulator.py | ROI/capacity | unknown | conditional | project provenance | E / REVIEW |

Dependency coverage of identified active consumers: **85%**. Binary reports, unindexed databases and generated historical outputs require manual provenance review.