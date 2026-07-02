# Reel Load Simulator — RC1 Release Notes

Release: RC1 (Release Candidate 1)
Date: 2026-06-30

Summary:
- Headless simulator runner validated and packaged as RC1.
- Included a smoke-test scenario (`scenario_rc1_smoketest.yaml`) and evidence artifacts.

Contents:
- `scripts/run_reel_rc1.py` — RC1 launcher
- `scripts/sanity_check_rc1.py` — safety checks and short-run validation
- `scripts/package_reel_rc1.py` — creates ZIP release
- `releases/reel_simulator_rc1_<ts>.zip` — packaged RC1
- `releases/rc1_evidence/` — validation evidence (logs, outputs, images)

Known limitations:
- Streamlit UI is available but expects a job API; interactive dashboard screenshots are generated from run outputs, not live UI captures.
- Full dependency set in `requirements.txt` is large; for RC1 only PyYAML is strictly required for the runner.

Notes for consumers:
- For quick demo, run `python scripts/run_reel_rc1.py --duration 30 --scenario ingetrans-reel-simulator/06_SCENARIOS/scenario_rc1_smoketest.yaml`.
- See `releases/RC1_CHECKLIST.md` for validation steps and acceptance criteria.
