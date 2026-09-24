# Pre-mortem Round 2 (2026-09-24)

Re-simulated the round-1 incident against the hardened plan:
- Scan at traffic lights → D-018 interlock refuses (T-S09); HANDOFF instructs stationary, ignition-on/engine-off scans. Residual: vehicle stopped at lights reports 0 km/h and the interlock allows the scan → documented residual (R-003 Medium).
- Clearing before an MOT → prompt spells out readiness reset; G-002 human sign-off; backup JSON. Residual Low.
- Clone adapter hang → per-read deadline + D-014 self-test → exit 3. Residual Low.
- Diesel PID crash → default list intersected with supported (S-012). Residual Low.
- Wrong VIN → D-017 + T-I01 asserts 17 characters. Residual Low.

Fresh look for new failure modes:
- G-003 is executed by a human who may skip the trace review → GATES.md makes the trace file part of the required evidence bundle. Medium (R-015).
- The public repository could receive a commit containing a real VIN or trace from G-003 evidence → HANDOFF/GATES: evidence files stay local; `.gitignore` covers `*.log`, `scan*.json`, `log*.csv`, `report*.html` (added this round). Low (R-016).

Round result: **0 Critical, 0 High.** Iteration stops (Phase 4.5).
