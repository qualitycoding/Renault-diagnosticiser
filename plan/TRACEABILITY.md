# Traceability

## Success criteria (measurable)
| SC | Criterion | Evidence | Steps |
|---|---|---|---|
| SC-1 | Adapter opens, passes self-test, reports version + voltage; generic EOBD read returns VIN, MIL, DTC count, stored/pending codes, readiness, protocol | T-U10, T-U10d, T-I01, T-I04 | S-006, S-007, S-012 |
| SC-2 | Renault ECU scan over the 9 ECUs of D-006: presence, session, UDS DTCs decoded (incl. multi-frame), KWP fallback count+raw | T-U01, T-U02, T-U02b, T-U03, T-U04, T-U04b, T-U04c, T-U05, T-U06, T-I02 | S-002, S-004, S-005, S-008 |
| SC-3 | Scan saved as schema-versioned JSON, exact round trip, atomic | T-U08, T-O06, T-I03 | S-009, S-012 |
| SC-4 | Self-contained HTML report, VIN masked by default | T-U09, T-I03, T-S05 | S-011, S-012 |
| SC-5 | Live CSV logging: resume, interrupt-safe, plots in report | T-O03, T-O04, T-O05, T-U09b, T-P01 | S-010, S-011 |
| SC-6 | Optional user description CSV, validated | T-U07 | S-005 |
| SC-7 | Read-only by construction; engine-code clear only with exact typed phrase + G-002 | T-S01, T-S01b, T-S02, T-S03, T-S04, T-S08, T-S09 | S-003, S-006, S-012 |
| SC-8 | Defined exit codes and messages for operational failures; scan resilience | T-O01, T-O02, T-O07 | S-008, S-012 |
| SC-9 | Performance: ≥ 50 samples/s logging overhead; worst-case 9-ECU scan ≤ 30 s | T-P01, T-P02 | S-010, S-012 |
| SC-10 | No known vulnerable dependency | CHK-01 | S-001, S-012 |
| SC-11 | Works on the user's car (human acceptance) | G-003 evidence | S-013 |
| SC-12 | Frozen tests unchanged | CHK-02 | every step |

## Test → requirement
| Test | Category | File | SC | Decisions / claims |
|---|---|---|---|---|
| T-U01 | unit | tests/unit/test_dtc.py | SC-2 | D-009, C-019 |
| T-U02, T-U02b | unit | tests/unit/test_dtc.py | SC-2 | D-009, C-013 |
| T-U06 | unit | tests/unit/test_dtc.py | SC-2 | D-009, C-022 |
| T-U07 | unit | tests/unit/test_dtc.py | SC-6 | D-010 |
| T-U03, T-U04, T-U04b, T-U04c | unit | tests/unit/test_parse.py | SC-2 | D-005, C-024, C-026 |
| T-U05 | unit | tests/unit/test_ecus_models_report.py | SC-2 | D-006, C-006 |
| T-U08 | unit | tests/unit/test_ecus_models_report.py | SC-3 | — |
| T-U09, T-U09b | unit | tests/unit/test_ecus_models_report.py | SC-4, SC-5 | D-011, D-016 |
| T-U10, T-U10b, T-U10c, T-U10d | unit | tests/unit/test_transport.py | SC-1, SC-8 | D-005, D-014 |
| T-I01..T-I04 | integration | tests/integration/test_emulator.py | SC-1..SC-4 | D-002, D-012, C-010 |
| T-O01..T-O07 | operational | tests/operational/test_operational.py | SC-3, SC-5, SC-8 | D-013 |
| T-S01..T-S04, T-S01b | security | tests/security/test_safety.py | SC-7 | D-004, C-018 |
| T-S05, T-S08 | security | tests/security/test_report_and_cli_security.py | SC-4, SC-7 | A-011, A-005 |
| T-S09 | security | tests/security/test_interlock.py | SC-7 | D-018, R-003 |
| T-P01, T-P02 | performance | tests/performance/test_performance.py | SC-9 | A-016, C-020 |

Pytest item count: 119 (parametrised). Categories: unit 31, integration 4, operational 7, security 75, performance 2.
