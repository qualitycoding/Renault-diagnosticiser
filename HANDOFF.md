# HANDOFF — Renault Scénic III OBD reader (`renault-diag`)

## Purpose
Build a read-only Python tool that reads generic EOBD data and Renault ECU fault codes from a 2016 Renault Scénic III through an OBDLink EX adapter, logs live data to CSV, and renders a self-contained HTML report. Hardware list: `plan/HARDWARE.md`.

## Active profiles
`software` only; `software.deploys = false` (`plan/PROFILE.md`).

## Reading order
1. `plan/PROFILE.md` 2. `plan/ASSUMPTIONS.md` 3. `plan/DECISIONS.md` (interfaces + decision rules) 4. `plan/PLAN.md` 5. `plan/GATES.md` 6. `plan/ENVIRONMENT.md` 7. `plan/TRACEABILITY.md` 8. `premortem/RISK_REGISTER.md` 9. `research/claims.json` as needed.

## Environment setup
See `plan/ENVIRONMENT.md` (literal, verified commands). Python 3.12 required.

## Run the frozen suite
```bash
. .venv/bin/activate
python -m pytest -q                 # target at the end of S-012: 119 passed
python -m pytest -q -m security     # category subsets: unit, integration, operational, security, performance
```

## Verify the freeze manifest
```bash
sha256sum -c tests/FROZEN_MANIFEST.sha256    # every line must read OK (Windows: use Git Bash or WSL)
```

## Steps at a glance
S-001 env → S-002 ECU table → S-003 safety allowlist → S-004 parser → S-005 DTC decode → S-006 transport → S-007 generic → S-008 manufacturer scan → S-009 JSON → S-010 logger → S-011 report → S-012 CLI + full suite + audit → S-013 **G-003** human real-car session → S-014 **G-002** merge to public main.

## Human gates
- **G-003** (S-013): the human runs the tool on the car; the implementer never touches the vehicle.
- **G-002** (S-014 and any real `clear-engine-codes` run): merge to the public `main` branch or clear engine codes only after explicit sign-off.
Definitions: `plan/GATES.md`.

## Real car (for the human, at G-003)
Ignition ON, engine OFF, vehicle stationary, parking brake on. Socket: centre console between the front seats. Then:
```bash
renault-diag ports
renault-diag check-adapter --port /dev/ttyUSB0          # Windows: COM3 etc.
renault-diag scan --port /dev/ttyUSB0 --out scan.json --trace trace.log
# start the engine for live data
renault-diag log --port /dev/ttyUSB0 --out log.csv --duration 60
renault-diag report --scan scan.json --log log.csv --out report.html
```
The ABS warning lamp may flash while the ABS module is being read (C-014); it should clear after the session / ignition cycle.

## Halt / deviation protocol
- Unanticipated situation → DR-09 in `plan/DECISIONS.md`.
- Frozen test believed wrong → stop, write `TEST_CHALLENGE.md` (item ID, evidence, proposed fix); the planning protocol is re-run.
- Blocked → `BLOCKED.md`; deviations → `DEVIATIONS.md`.
- Any request outside the D-004 allowlist seen in a trace → Critical, halt (DR-08).

## Integrity rule (Rule 9, verbatim)
> **Integrity** `[All]`: No step may fabricate, cherry-pick without disclosure, or manually alter data, test results, benchmarks, or figures. In addition:
> * `[computational, publication]` Every reported number is generated from committed results, not transcribed by hand.
> * `[publication]` Generative-AI images are never used as data figures. AI assistance is disclosed according to the venue's policy, as recorded in `plan/ASSUMPTIONS.md`.

(The two bracketed sub-rules are N/A for this `software`-only plan.)
