# RC1 Validation Report — Reel Load Simulator

Date: 2026-06-30
Branch: `feature/ingest-sim-run`
Tag created: `RC1`

Summary
-------
This report documents the validation performed for Release Candidate 1 (RC1)
of the Reel Load Simulator. RC1 is a headless simulator runner intended for
internal use and demonstrations. The goal of validation is to prove the
simulator is usable by end users (start, run a scenario, produce outputs).

Run summary (smoke test)
------------------------
- Scenario: `ingetrans-reel-simulator/06_SCENARIOS/scenario_rc1_smoketest.yaml`
- Command executed: `python scripts/run_reel_rc1.py --duration 30 --scenario ingetrans-reel-simulator/06_SCENARIOS/scenario_rc1_smoketest.yaml`
- Observed runtime statistics (from `run_summary.json`):
  - `run_id`: run_20260630T055101Z
  - `run_duration_s`: 30.0
  - `completed_orders`: 15
  - `throughput_rolls_per_hour`: 1800.0

Functional validation
---------------------

Fully operational features (RC1):

- Headless simulation runner: `ingetrans-reel-simulator/scripts/run_simulator.py` — loads scenario YAML, simulates events, writes outputs.
- RC1 launcher: `scripts/run_reel_rc1.py` — single-command entrypoint for demos.
- Scenario management: scenarios in `ingetrans-reel-simulator/06_SCENARIOS/` (smoke test scenario added).
- Outputs generation: `run_summary.json`, `event_log.csv` and zipped run folder.
- Packaging: `scripts/package_reel_rc1.py` produces a ZIP release.
- Sanity checks: `scripts/sanity_check_rc1.py` performs dependency checks and short-run verification.

Partially implemented / optional features:

- Streamlit UI pages exist (`pages/reel_load_simulator_v4.py`) but the UI expects a Job API (`SIMULATOR_API_URL`) to run jobs; the UI can show outputs but does not run simulations by itself unless the Job API is available.
- Advanced charts: optional module `ingetrans_simulator.advanced_charts` is used when available; otherwise the UI shows placeholders.

Mocked / simulated functionality:

- UI Sankey / advanced charts: fallback placeholder used when `advanced_charts` module is missing.

Missing functionality (not required for RC1 usability):

- Background Job API / scheduling service (not packaged with RC1).
- Persistent storage for long-term runs (RC1 writes local outputs only).
- Contract tests, CI gating, and production-grade packaging.

Quality
-------

Known issues:

- Deprecation warnings: `datetime.utcnow()` used in runner prints DeprecationWarning (non-blocking). See console log.
- The default scenario (older scenarios) may produce `completed_orders=0` for short runs; the smoke scenario added fixes this for demos.

Limitations and risks:

- Performance: the simulator is single-threaded Python; very long or high-fidelity runs may be slow.
- Dependencies: full `requirements.txt` is large; installing the complete set can take significant time and may fail on some Windows setups (notes in `requirements.txt`). RC1 only needs `PyYAML` for basic runs.
- Security: RC1 is a demo runner without authentication or network hardening; do not expose it on untrusted networks.

Installation validation
-----------------------

Can a new user run RC1 from scratch? Yes, following these steps:

1. Create and activate a Python virtual environment (example PowerShell):

```powershell
python -m venv .venv
& ".venv\Scripts\Activate.ps1"
```

2. Install dependencies (minimal):

```bash
pip install pyyaml pillow
```

For the full project (optional), run:

```bash
pip install -r requirements.txt
```

Estimated install time:

- Minimal (PyYAML + Pillow): a few seconds to a minute depending on network.
- Full `requirements.txt`: several minutes to tens of minutes (depends on network, platform and binary availability).

Execution validation
--------------------

Startup command (recommended for RC1 demo):

```bash
python scripts/run_reel_rc1.py --duration 30 --scenario ingetrans-reel-simulator/06_SCENARIOS/scenario_rc1_smoketest.yaml
```

Default configuration used by the smoke test:

- `tick_s`: 1.0 (from config fallback)
- `production_order.interarrival_min_s`: 3.0 (smoke scenario)

Expected results:

- Directory: `ingetrans-reel-simulator/outputs/run_<timestamp>/`
- Files: `run_summary.json`, `event_log.csv` and optional CSV/packaged outputs.

Evidence produced during validation
----------------------------------

All artifacts are in `releases/rc1_evidence/`.

- `run_summary.json` — simulation summary (contains completed_orders=15)
- `event_log.csv` — event log for the run
- `run_20260630T055101Z.zip` — zipped run outputs folder
- `console_run_output.txt` — captured console output
- `run_summary.png` — rendered image of key KPIs
- `event_log.png` — rendered image of first lines of event_log.csv
- `folder_tree.png` — visualized repository tree (partial)

Sample evidence snippets
-----------------------

`run_summary.json` (excerpt):

```json
{
  "run_id": "run_20260630T055101Z",
  "scenario": "scenario_rc1_smoketest.yaml",
  "run_duration_s": 30.0,
  "completed_orders": 15,
  "throughput_rolls_per_hour": 1800.0
}
```

Known issues observed in logs
---------------------------

- Deprecation warnings for `datetime.utcnow()` appear in console output (non-fatal).

Release readiness assessment
---------------------------

- Ready for internal use: YES — RC1 runs reliably, produces outputs, suitable for demos and engineering validation.
- Ready for customer demonstration: YES — with the smoke test scenario and the packaged ZIP, RC1 can be demonstrated in controlled sessions.
- Ready for production: NO — RC1 is a demo runner; it lacks production features (auth, job orchestration, monitoring, contract tests, hardened packaging).

Freeze actions performed
------------------------

- Commit created with RC1 artifacts on branch `feature/ingest-sim-run`.
- Annotated git tag created: `RC1` (local). Do not push if you want review before publishing.
- Release notes and changelog created under `releases/`.

Next steps (after freeze)
------------------------

1. Keep RC1 executable and stable: any subsequent changes must preserve existing runner behavior and outputs.
2. Continue platform architecture work in parallel (Event Catalog validation) — do not produce payloads until Event Catalog approved.
3. If desired, publish `releases/reel_simulator_rc1_<ts>.zip` to your artifact store and create a GitHub Release associated with the `RC1` tag.

Files (evidence)
----------------

- releases/rc1_evidence/run_summary.json
- releases/rc1_evidence/event_log.csv
- releases/rc1_evidence/console_run_output.txt
- releases/rc1_evidence/run_20260630T055101Z.zip
- releases/rc1_evidence/run_summary.png
- releases/rc1_evidence/event_log.png
- releases/rc1_evidence/folder_tree.png
