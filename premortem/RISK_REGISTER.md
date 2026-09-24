# Risk Register

Severity after mitigation (per Rule 4 rubric; `software` lines apply). Likelihood: L/M/H.

| ID | Description | Lens | Severity (before → after) | Likelihood | Root cause | Traces to | Mitigation |
|---|---|---|---|---|---|---|---|
| R-001 | Research/cold-read/pre-mortem reviews were not done by independent fresh-context agents | Invalid assumptions | Medium → Medium | M | No subagent capability (A-010) | A-010, all phases | Logged; human may re-run cold read with an independent agent before S-001 |
| R-002 | Tool transmits a non-read-only service or adapter-EEPROM command | Security | Critical → Low | L | Allowlist bug or bypass | D-004, S-003, S-006 | Check-before-write; T-S01..T-S04, T-S01b; DR-08 trace review at G-003 |
| R-003 | Manufacturer session opened while driving; ABS/ESP lamp or degraded ESP | Security (vehicle safety) | Critical → Medium | L | User runs scan in motion | C-014, A-018 | D-018 interlock (T-S09); residual: stopped-in-traffic still allowed; HANDOFF instructions |
| R-004 | Scénic III ECU IDs differ from the Mégane III (X95) table | Invalid assumptions | High → Medium | M | No J95-specific source | C-006, D-006 | D-013 (absent ≠ failure); G-003 review; DR-06 |
| R-005 | Wrong protocol assumption per ECU / 10 C0 rejected | Invalid assumptions | Medium → Low | M | Single-source C-007, C-012 | D-007, D-008 | UDS→KWP fallback; session NRC tolerated (T-I02) |
| R-006 | Default PID list includes PIDs unsupported by the K9K diesel | Technical | High → Low | H | Petrol-centric defaults | S-012 | Intersect with supported set, warn |
| R-007 | Battery drained by long ignition-on sessions | Operational | Medium → Medium | M | User behaviour | HARDWARE.md | Voltage warning < 12.0 V; HANDOFF advice; maintainer suggested |
| R-008 | Clearing codes erases evidence / resets readiness before MOT | Operational (unrecoverable state) | Critical → Low | L | Irreversible action | A-005, S-012 | Backup JSON, consequence text, exact phrase (T-S08), G-002 |
| R-009 | Dependency drift or yanked release (python-OBD 0.x, emulator 4.0.0) | Supply chain | High → Medium | M | Young/0.x packages | ENVIRONMENT.md | Hash pins; DR-01, DR-02; CHK-01 |
| R-010 | Emulator licence (CC-BY-NC-SA-4.0) conflicts with future commercial use | Supply chain | Medium → Low | L | Licence | C-015, D-012 | Dev-only, never vendored |
| R-011 | `sha256sum` missing on Windows | Operational | Low → Low | M | Platform | HANDOFF | Use Git Bash / WSL |
| R-012 | Real adapter output differs from emulator/fake (extra status lines, timing) | Implementer misinterpretation | High → Medium | M | Emulator ≠ car (C-026) | D-005, S-004 | Parser fails closed; `--trace`; G-003 |
| R-013 | HTML report script injection via ECU/adapter/description strings | Security | High → Low | L | Untrusted strings | D-011 | html.escape; T-S05 |
| R-014 | GitHub PAT exposed in the planning chat transcript | Security | High → Medium | M | Credential pasted in chat | A-001 | Never written to repo; human must revoke after this run |
| R-015 | Human skips trace review at G-003 | Operational | Medium → Medium | M | Manual gate | G-003 | Trace file mandatory in evidence bundle |
| R-016 | Personal data (VIN, traces) committed to the public repo | Security | Medium → Low | L | Evidence files near repo | A-012 | `.gitignore` patterns; evidence stays local |
| R-017 | Unresolved single-source non-load-bearing claims (C-007, C-012, C-014, C-022) | Invalid assumptions | Low → Low | M | Sparse sources | research | Designs do not depend on them |

Counts after mitigation: Critical 0, High 0, Medium 8, Low 9.
