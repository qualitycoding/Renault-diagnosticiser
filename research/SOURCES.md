# Sources (with verification notes)

| # | Source | Tier | Version / date | How verified | Used by |
|---|---|---|---|---|---|
| 1 | python-OBD docs, https://python-obd.readthedocs.io/ | 1 | 0.7.3 | Read; confirmed by spike S1 | C-001 |
| 2 | PyPI JSON for obd, ELM327-emulator, pytest, pip-audit | 1 | 2026-09-24 | Fetched via curl in sandbox | C-001, C-015 |
| 3 | obd 0.7.3 wheel source (`obd/__init__.py` header) | 1 | 0.7.3 | Downloaded and grepped | C-003 |
| 4 | DDT4all source, https://github.com/cedricp/ddt4all | 1 | commit d05e0608 (2026-09-22) | Cloned; files/lines cited in claims | C-004, C-006, C-008, C-009, C-011, C-012, C-016, C-018, C-022, C-023 |
| 5 | pyren wiki "Getting started", gitlab.com/py_ren/pyren | 3 | 2018 page | Search snippet (page is JS-rendered; fetch returned no body) | C-004, C-006, C-007 |
| 6 | ELM327 datasheet ELM327DSF.pdf, elmelectronics.com | 1 | DSF rev. | Search snippet of AT command summary | C-011, C-024 |
| 7 | udsoncan ReadDTCInformation source/docs | 1 | 1.26.1 | Read module source excerpt | C-013 |
| 8 | Medium: UDS DTC sub-functions part 2 | 3 | 2025-11 | Read | C-013 |
| 9 | Klavkarr OBD socket pages (Scénic 3, Scénic 3 armrest, Scénic 4) | 3 | undated | Read | C-005 |
| 10 | OBDLink EX product page; OBDadvisor review; Gendan listing | 1/3/4 | 2026 | Read | C-017 |
| 11 | DDT4all issues #415, discussion #1120 | 2/4 | 2020, 2024 | Read | C-014, C-016 |
| 12 | LKML can327 driver documentation | 2 | 2022 | Read | C-024 |
| 13 | Wikipedia ELM327 | 3 | current | Read | C-016 |
| 14 | obdii365 DDT4all guide | 4 | undated | Read (only as corroboration of a Tier-1 repo observation) | C-009 |
| 15 | Spikes S1–S5 + pip-audit (this repo, `research/spikes/`) | 1 (empirical) | 2026-09-24 | Executed in sandbox, output committed | C-002, C-008, C-010, C-011, C-019, C-020, C-021, C-025 |
