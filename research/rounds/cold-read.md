# Phase 3.6 Cold-Read Gate log

Tier substitution (A-010): each pass was a dry run of `HANDOFF.md` + `plan/PLAN.md` by the orchestrator, reading only branch contents, plus the mechanical checker `research/spikes/consistency_check.py`. Where a frozen test's feasibility was in doubt, it was checked empirically against the emulator (spikes S7–S9) rather than by reading.

| Pass | Items found | Resolution |
|---|---|---|
| 1 | (1) T-I01 infeasible via python-OBD `value` (VIN truncated to 13 chars, C-027); (2) T-S08 infeasible if `serial_factory` default is bound at import; (3) content of the pre-clear backup unspecified; (4) `check-adapter` output format unspecified; (5) `--trace` used in G-003 but absent from the interface; (6) S-007 wording of stored vs pending DTC commands unclear | (1) D-017 + S-007; (2) interface: `serial_factory=None` resolved at `open()`; (3)(4)(5) interface text in DECISIONS; (6) S-007 reworded |
| 2 | Checker: two dangling test IDs in QUESTIONS.md and claims.json (a fifth integration test and a pip-audit test that do not exist), N/A paths flagged from PROFILE | References fixed; checker excludes PROFILE's N/A list |
| 3 (after Phase 4 round 1 changes) | T-S09 fixture validity (stock emulator speed is 10 km/h) | Stationary SPEED override in conftest, validated by spike S9; exit-4 condition made precise |
| 4 | Checker `OK: 0 items`; dry run: no questions, undefined terms, missing inputs or unstated credentials | Gate passed |
