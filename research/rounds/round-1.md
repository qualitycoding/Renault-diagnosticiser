# Research Round 1 (2026-09-24)

**R1 Decompose:** question tree written (`research/QUESTIONS.md`).

**R2 Breadth:** web searches on python-OBD, DDT4all/pyren ECU addressing, OBD socket location, OBDLink EX, ELM327 datasheet, UDS 0x19. Cloned DDT4all at d05e0608 to read the address tables and ELM command sequence directly (Tier 1). Claims C-001..C-007, C-009, C-011, C-012, C-014, C-016..C-018 recorded.

**R3 Synthesis / gaps:**
- C-007 (protocol type per ECU) is single-source and would change which DTC service is used → design change: probe UDS first, fall back to KWP (D-008), so C-007 is no longer load-bearing.
- C-012 (10 C0 session) single-source → decision rule D-007 continues in default session on NRC, so not load-bearing.
- New question: can we test Renault addressing without a car? → Q3.1.
- New question: licence of any emulator → Q3.3.

**R4 Depth:** C-006 checked in DDT4all `projects.json` (Tier 1) in addition to the pyren wiki. C-011 checked against the ELM327 datasheet.

**R5 Adversarial (same agent, explicit disproof attempt — see A-010):**
- Tried to disprove C-006 for Scénic III specifically: DDT4all has no separate J95 project; Scénic III shares the X95 (Mégane III) platform. Residual risk logged (R-004); runtime behaviour does not depend on it being exact because absent ECUs are reported as "no response" (D-013).
- Tried to disprove "OBDLink EX works with Renault": found only Ford-centric marketing; DDT4all README explicitly lists EX as tested. Kept corroborated.
- Found clone-adapter limitation (Wikipedia: clones limited to v1.4 functions; ATCRA needs v1.3+) → added adapter self-test (D-014).

**R6 Empirical:** spikes S1 (python-OBD ↔ emulator), S2 (raw AT dialogue), S5 (DTC decoding).

New load-bearing claims this round: 14. Continue.
