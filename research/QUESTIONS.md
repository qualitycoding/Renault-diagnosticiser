# Question Tree (R1)

Only the `software` branch is active (see `plan/PROFILE.md`). Each leaf names what it informs; leaves informing nothing were pruned (listed at bottom).

## Q1 Engineering — talking to the car
- Q1.1 Which Python library gives reliable generic OBD-II over ELM327, and is it maintained/licensed compatibly? → D-002, A-017 (C-001, C-002, C-003)
- Q1.2 What bus/bit-rate do the Scénic III ECUs use? → D-005 (C-004)
- Q1.3 Which CAN IDs address each Renault ECU? → D-006, T-U05 (C-006, C-008)
- Q1.4 Which diagnostic protocol (UDS vs KWP) does each ECU speak? → D-008 (C-007, C-022, C-023)
- Q1.5 Which ELM327 commands address an arbitrary ECU and handle multi-frame replies? → D-005, T-U07 (C-011, C-024)
- Q1.6 What session must be opened first? → D-007 (C-012)
- Q1.7 How are UDS and OBD DTCs encoded? → D-009, T-U01, T-U02 (C-013, C-019)
- Q1.8 Can Renault text descriptions be shipped? → A-004, D-010 (C-009)

## Q2 Engineering — safety & security
- Q2.1 Which services are read-only and safe to allow? → D-004, T-S01..T-S03 (C-018)
- Q2.2 Are there known side-effects of read-only sessions on this car family? → A-018 (C-014)
- Q2.3 Do pinned dependencies carry known vulnerabilities? → T-S06 (C-021)

## Q3 Engineering — testing without a car
- Q3.1 Can an emulator stand in for the adapter + car, including Renault-style headers? → D-012, T-I01..T-I05 (C-002, C-010)
- Q3.2 What is the emulator throughput, so perf tests measure our code, not the emulator? → A-016, T-P01, T-P02 (C-020)
- Q3.3 Is the emulator licence compatible with our use? → A-017, D-012 (C-015)

## Q4 Hardware
- Q4.1 Which adapter reliably reaches Renault CAN modules? → A-009, HARDWARE.md (C-016, C-017)
- Q4.2 Where is the diagnostic socket? → HARDWARE.md (C-005)

## Q5 Operations (local tool)
- Q5.1 Can the environment be hash-pinned and installed reproducibly? → ENVIRONMENT.md (C-025)

## Pruned
- CAN sniffing of raw (non-diagnostic) frames — informs nothing in scope (A-004).
- Android app frameworks — platform fixed by A-006.
- DoIP — not present on 2016 Scénic.
