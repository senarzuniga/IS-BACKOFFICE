# RC1 Release Checklist — Reel Load Simulator

Purpose: provide a small checklist to validate and ship RC1 (executable headless runner).

- [ ] Run `scripts/sanity_check_rc1.py` (default runs a short 2s simulation):
  - `python scripts/sanity_check_rc1.py`
  - Or skip execution and only check files: `python scripts/sanity_check_rc1.py --no-run`
- [ ] If sanity check passes, create the package:
  - `python scripts/package_reel_rc1.py` (creates `releases/reel_simulator_rc1_<ts>.zip`)
- [ ] Verify the created ZIP by extracting and running `run_reel_rc1.py --duration 5`
- [ ] Add acceptance notes and attach the ZIP to the RC1 release in the repo or artifact store.
- [ ] Create a small CHANGELOG entry summarizing fixes and known limitations.

Known limitations (RC1):
- Minimal runner: not all telemetry or advanced charts included.
- Streamlit UI and Job API are optional and not part of the RC1 ZIP.

Sign-off:

- Product owner: ____________________  Date: ________
- Architect: ________________________  Date: ________
