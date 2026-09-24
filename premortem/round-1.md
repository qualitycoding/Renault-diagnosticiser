# Pre-mortem Round 1 (2026-09-24)

Reviewer: orchestrator acting as a non-author adversarial reviewer (tier substitution, A-010 / R-001).

## Incident report — six months after release
> The user plugged the tool into the Scénic, ran `renault-diag scan` while sitting at traffic lights on the way to work "to see live values". The ABS module entered its after-sales session, the ABS/ESP lamp flashed and ESP was degraded until the ignition cycle (C-014). Separately, a week later the user ran `clear-engine-codes` to clear an intermittent glow-plug code the night before the MOT; readiness monitors reset and the car failed the emissions check. On a Windows laptop the tool hung forever on a cheap Bluetooth clone the user borrowed. The live logger crashed immediately on the diesel K9K because the default PID list included a petrol-only PID. Finally, python-OBD reported a 13-character VIN, so the report was wrong.

## Lens review
| Lens | Findings |
|---|---|
| Technical correctness | VIN truncation in python-OBD (found in cold read, C-027) → D-017 already applied. Real STN adapters can emit lines not seen in the emulator (`STOPPED`, `<DATA ERROR`) → parser must fail closed (R-012). |
| Dependency / supply-chain drift | python-OBD is 0.x; emulator 4.0.0 is one week old (R-009). |
| Invalid research assumptions | C-006 (ECU table from Mégane III), C-007 (protocol type), C-012 (10 C0), C-014 are single-source or platform-inferred (R-004, R-005). |
| Implementer misinterpretation | Fake-based tests may pass with an implementation that mishandles real timing (R-012); interface ambiguity around exit 4 fixed in D-### cli. |
| Integrity (Rule 9) | No data/figures published; risk only if an implementer edits frozen tests — CHK-02 on every step. |
| Scale & performance | Real ELM ≈ 10–30 queries/s; our target is overhead only (A-016). Hang on dead adapter → every read has a deadline `timeout_s` (S-006). |
| Security | Vehicle-safety: moving-vehicle use (R-003, Critical before mitigation); unintended writes (R-002); HTML injection (R-013); credential leakage (R-014). |
| Operational realities | Battery drain (R-007); irreversible code clearing (R-008); Windows lacks `sha256sum` (R-011). |

## New mitigations applied in this round
- **R-003** → D-018 moving-vehicle interlock + new frozen test **T-S09** (Phase 2 re-run: unfrozen, added, red-verified 119 failed/0 errors, re-frozen) + cold-read re-run.
- **R-008** → clear prompt states consequences; backup before clear; G-002 applies to every real clear.
- **R-006** → CLI `log` default PIDs intersected with supported set (S-012 step 4).
- **R-002** → check-before-write is tested (T-S01b); DR-08 on traces at G-003.

Result: after mitigations, Critical 0, High 0 (see register); a second round is still required to confirm.
