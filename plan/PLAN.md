<!-- STATUS HEADER (Phase 5.2) -->
**STATUS: READY**
- Active profiles: `software` (`software.deploys = false`)
- Claims: 27 total — verified 15, corroborated 8, single-source 4 (none load-bearing), inferred 0
- Tests (frozen, red at freeze): 119 — unit 31, integration 4, operational 7, security 75, performance 2; checks CHK-01, CHK-02
- Steps: 14 (S-001–S-014)
- Gates: 2 applicable (G-002, G-003); G-001 N/A
- Risks after mitigation: Critical 0, High 0, Medium 8, Low 9

# Execution Plan


Implementation happens on a new branch `impl/renault-diag` created from this generation branch. Tests are frozen: never modify, skip, xfail or weaken them (Immutability Rule). Deviations go in `DEVIATIONS.md`; blockers in `BLOCKED.md`; invalid tests in `TEST_CHALLENGE.md`.

**Resume rule:** on restart, read `.checkpoints/impl_state.json` (create it in S-001 as `{"done": []}`), skip steps listed in `done`, and re-run the first missing step — every step is idempotent (it only rewrites its own output files).

## Checks
- **CHK-01 (dependency scan):** `pip-audit -r requirements.txt && pip-audit -r requirements-dev.txt` → exit 0.
- **CHK-02 (freeze):** `sha256sum -c tests/FROZEN_MANIFEST.sha256` → all `OK`.


### S-001 Environment setup and freeze verification
- Tier: Sonnet
- Profile: software
- Depends on: none
- Inputs: repo checkout
- Actions:
  1. `python3.12 -m venv .venv && . .venv/bin/activate`
  2. `pip install --require-hashes -r requirements.txt -r requirements-dev.txt`
  3. `pip install --no-deps --no-build-isolation -e .`
  4. `sha256sum -c tests/FROZEN_MANIFEST.sha256` — every line must end `OK`.
  5. `python -m pytest -q` — expect `119 failed` (red baseline) and 0 errors.
- Outputs: .venv/ (untracked)
- Evidence produced: none
- Done when: `sha256sum -c` all OK; pytest summary `117 failed`; CHK-02 still passes
- Checkpoint: append `S-001` to `.checkpoints/impl_state.json` `done`; commit `impl: S-001 Environment setup and freeze verification`
- On failure: DR-01; if manifest check fails → halt `BLOCKED.md` (frozen tests altered).
- Gate: none
- Relevant decisions/claims: D-015, C-025

### S-002 ECU table
- Tier: Haiku
- Profile: software
- Depends on: S-001
- Inputs: src/renault_diag/ecus.py, plan/DECISIONS.md D-006
- Actions:
  1. Replace `SCENIC3_ECUS = ()` with the nine `EcuDef` entries exactly as in D-006 (same order, labels free-text).
  2. Implement `ecu_by_name` (case-insensitive search over `SCENIC3_ECUS + (FUNCTIONAL_OBD,)`, else `ValueError`).
- Outputs: src/renault_diag/ecus.py
- Evidence produced: T-U05
- Done when: `pytest -q -k T_U05` passes; CHK-02 still passes
- Checkpoint: append `S-002` to `.checkpoints/impl_state.json` `done`; commit `impl: S-002 ECU table`
- On failure: Retry once; else halt `BLOCKED.md`.
- Gate: none
- Relevant decisions/claims: D-006, C-006

### S-003 Safety allowlist
- Tier: Opus
- Profile: software
- Depends on: S-002
- Inputs: src/renault_diag/safety.py, D-004
- Actions:
  1. Implement `check_request` exactly per D-004 (service byte = payload[0]; subfunction rules for 0x10 and 0x19; 0x3E length ≤ 2; empty payload forbidden; 0x04/0x14 only with `allow_clear=True` and `target.tx_id in (0x7E0, 0x7DF)`).
  2. Implement `check_at_command`: normalise by removing spaces and upper-casing; strip a leading `AT` if present; allow exact tokens and regexes `SH[0-9A-F]{3}`, `CRA([0-9A-F]{3})?`, `FCSH[0-9A-F]{3}`, `FCSD300000`, `FCSM1`, `ST[0-9A-F]{2}`; reject everything else, including any input that starts with `ST` followed by letters.
  3. Raise `ForbiddenRequestError` with a message naming the rejected service/command.
- Outputs: src/renault_diag/safety.py
- Evidence produced: T-S01, T-S02, T-S03, T-S04
- Done when: `pytest -q tests/security/test_safety.py -k 'not T_S01b'` passes; CHK-02 still passes
- Checkpoint: append `S-003` to `.checkpoints/impl_state.json` `done`; commit `impl: S-003 Safety allowlist`
- On failure: If a frozen test seems to contradict D-004 → `TEST_CHALLENGE.md`, halt.
- Gate: none
- Relevant decisions/claims: D-004, C-018, A-005

### S-004 ELM response parser
- Tier: Opus
- Profile: software
- Depends on: S-001
- Inputs: src/renault_diag/elm_parse.py, D-005 interface
- Actions:
  1. Split `text` on `\r`/`\n`; drop blanks, `SEARCHING...`, `OK`, and echo lines.
  2. If any line contains `BUFFER FULL` → `BufferFullError`; exact terminal messages per interface → mapped errors.
  3. Parse frame lines: optional spaces; 3 hex-digit ID followed by data bytes (spaces-off form: first 3 chars = ID). Keep frames whose ID == `rx_id`.
  4. ISO-TP: PCI high nibble 0 = SF (len = low nibble), 1 = FF (len = 12 bits), 2 = CF (sequence 1..F then 0, must increment); assemble messages; truncate to declared length; incomplete message or bad sequence → `ProtocolError`.
  5. Apply the response-pending rule from the interface; no frames for `rx_id` → `ProtocolError`.
- Outputs: src/renault_diag/elm_parse.py
- Evidence produced: T-U03, T-U04, T-U04b, T-U04c
- Done when: `pytest -q tests/unit/test_parse.py` passes; CHK-02 still passes
- Checkpoint: append `S-004` to `.checkpoints/impl_state.json` `done`; commit `impl: S-004 ELM response parser`
- On failure: Retry with Opus; after 3 failed attempts halt `BLOCKED.md`.
- Gate: none
- Relevant decisions/claims: D-005, C-011, C-024, C-026

### S-005 DTC decoding and descriptions
- Tier: Sonnet
- Profile: software
- Depends on: S-001
- Inputs: src/renault_diag/dtc.py, D-009, D-010
- Actions:
  1. Implement `decode_obd_pair`, `decode_uds_19_02`, `decode_kwp_17`, `status_flags`, `load_descriptions` exactly per the interface text.
  2. `decode_uds_19_02`: require `payload[0]==0x59 and payload[1]==0x02 and len>=3`; iterate 4-byte records from index 3; skip records whose 3-byte DTC is 0; trailing bytes (<4) allowed only if all zero, else `ProtocolError`.
  3. `load_descriptions`: `csv.reader`, header must equal `['code','description']`.
- Outputs: src/renault_diag/dtc.py
- Evidence produced: T-U01, T-U02, T-U02b, T-U06, T-U07
- Done when: `pytest -q tests/unit/test_dtc.py` passes; CHK-02 still passes
- Checkpoint: append `S-005` to `.checkpoints/impl_state.json` `done`; commit `impl: S-005 DTC decoding and descriptions`
- On failure: DR-09
- Gate: none
- Relevant decisions/claims: D-009, D-010, C-013, C-019, C-022

### S-006 ELM327 transport
- Tier: Opus
- Profile: software
- Depends on: S-003, S-004
- Inputs: src/renault_diag/transport.py, D-005, D-014
- Actions:
  1. `open()`: resolve `factory = self.serial_factory or serial.Serial` at call time; call `factory(port, baudrate, timeout=timeout_s)`; `serial.SerialException`/`OSError` → `AdapterNotFoundError`. Send `ATZ, ATE0, ATL0, ATS1, ATH1, ATSP6, ATAL, ATCAF1, ATCFC1`; read each reply up to `>` (loop on `read`/`read_until(b'>')`, overall deadline `timeout_s`); `ATI` → version; self-test `ATCRA7E8` must reply `OK` then send `ATCRA` (reset); `ATRV` → voltage via regex `([0-9.]+)V`.
  2. Every AT command goes through `safety.check_at_command` first; `request` calls `safety.check_request` **before** any write, including header commands.
  3. Track current ECU; on change send `ATSH, ATCRA, ATFCSH, ATFCSD300000, ATFCSM1`.
  4. Send payload as uppercase hex; parse with `parse_response(text, ecu.rx_id)`; handle `7F` (NRC 0x78 → re-send, ≤10), negative → `NegativeResponseError`; positive SID must equal request SID + 0x40.
  5. Optional `trace_path` keyword (default `None`) appends `>> cmd` / `<< reply` lines.
- Outputs: src/renault_diag/transport.py
- Evidence produced: T-U10, T-U10b, T-U10c, T-U10d, T-S01b
- Done when: `pytest -q tests/unit/test_transport.py tests/security/test_safety.py` passes; CHK-02 still passes
- Checkpoint: append `S-006` to `.checkpoints/impl_state.json` `done`; commit `impl: S-006 ELM327 transport`
- On failure: DR-09; never weaken the check-before-write order.
- Gate: none
- Relevant decisions/claims: D-003, D-004, D-005, D-014

### S-007 Generic OBD report
- Tier: Sonnet
- Profile: software
- Depends on: S-005
- Inputs: src/renault_diag/generic.py, python-OBD 0.7.3 docs
- Actions:
  1. `read_generic(conn)`: VIN per D-017 from `conn.query(obd.commands.VIN, force=True).messages[0].data[3:20]` (ASCII, strip non-alphanumerics; `None` if absent), `STATUS` → `mil_on = status.MIL`, `dtc_count = status.DTC_count`; readiness from each `status.<test>` object (`available`/`complete` → `complete|incomplete|unavailable`, keyed by test name); stored = `obd.commands.GET_DTC` (mode 03), pending = `obd.commands.GET_CURRENT_DTC` (mode 07); each `(code, desc)` → `Dtc(code, None, 'obd', code)`; `protocol = conn.protocol_name()`; `supported = sorted(c.name for c in conn.supported_commands)`.
  2. Use `force=True` only for VIN.
- Outputs: src/renault_diag/generic.py
- Evidence produced: T-I01
- Done when: `pytest -q -k T_I01` passes; CHK-02 still passes
- Checkpoint: append `S-007` to `.checkpoints/impl_state.json` `done`; commit `impl: S-007 Generic OBD report`
- On failure: DR-03
- Gate: none
- Relevant decisions/claims: D-002, D-017, C-001, C-002, C-027

### S-008 Manufacturer scan
- Tier: Opus
- Profile: software
- Depends on: S-006
- Inputs: src/renault_diag/manufacturer.py, D-007, D-008, D-013
- Actions:
  1. `scan_ecu`: send `10 C0`; `NoResponseError` → `EcuResult(present=False, error='no response')`; `NegativeResponseError` → `session_ok=False`, continue; `BusError`/`ProtocolError`/`BufferFullError` → `present=False`, `error=str(exc)`.
  2. Send `19 02 AF` → `protocol='uds'`, decode; if `NegativeResponseError` with nrc in (0x11, 0x12) → send `17 FF 00` → `protocol='kwp'`, `decode_kwp_17`.
  3. `scan_all`: iterate in order; let `AdapterNotFoundError` propagate; any other `DiagError` recorded on that ECU.
- Outputs: src/renault_diag/manufacturer.py
- Evidence produced: T-I02, T-O07
- Done when: `pytest -q -k 'T_I02 or T_O07'` passes; CHK-02 still passes
- Checkpoint: append `S-008` to `.checkpoints/impl_state.json` `done`; commit `impl: S-008 Manufacturer scan`
- On failure: DR-06 semantics; DR-09
- Gate: none
- Relevant decisions/claims: D-007, D-008, D-013

### S-009 JSON model
- Tier: Sonnet
- Profile: software
- Depends on: S-005, S-007, S-008
- Inputs: src/renault_diag/models.py
- Actions:
  1. `to_json`: `dataclasses.asdict` → `json.dumps(indent=2, sort_keys=True)`.
  2. `from_json`: rebuild nested dataclasses (`Dtc`, `GenericReport`, `EcuResult`); reject `schema_version != 1` with `ValueError`.
  3. `write_json_atomic`: write to `tempfile.NamedTemporaryFile(dir=path.parent, delete=False)`, flush+fsync, `os.replace`; on any exception delete the temp file and re-raise.
- Outputs: src/renault_diag/models.py
- Evidence produced: T-U08, T-O06
- Done when: `pytest -q -k 'T_U08 or T_O06'` passes; CHK-02 still passes
- Checkpoint: append `S-009` to `.checkpoints/impl_state.json` `done`; commit `impl: S-009 JSON model`
- On failure: DR-09
- Gate: none
- Relevant decisions/claims: A-013

### S-010 Live logger
- Tier: Sonnet
- Profile: software
- Depends on: S-001
- Inputs: src/renault_diag/logger.py
- Actions:
  1. Validate every PID name against `{c.name for c in conn.supported_commands}` before touching the file; else `ValueError`.
  2. Header `timestamp_utc,elapsed_s,` + PIDs. Existing file: first line must equal header (else `ValueError`, no write) → append, `resumed=True`.
  3. Loop: check `stop_event`, limits; build `cmd_map = {c.name: c for c in conn.supported_commands}` once and query `conn.query(cmd_map[name])` for each PID (works for python-OBD and the test fakes); write the row only after all PIDs succeeded; `value.magnitude` if present else value; `None` → empty cell; flush every row, `os.fsync` every 10 rows; `sleep(interval_s)`.
  4. `KeyboardInterrupt` → stop with `stopped_by='interrupt'` (partial row discarded).
- Outputs: src/renault_diag/logger.py
- Evidence produced: T-O03, T-O04, T-O05, T-P01
- Done when: `pytest -q -k 'T_O03 or T_O04 or T_O05 or T_P01'` passes; CHK-02 still passes
- Checkpoint: append `S-010` to `.checkpoints/impl_state.json` `done`; commit `impl: S-010 Live logger`
- On failure: DR-05 for T-P01
- Gate: none
- Relevant decisions/claims: A-016, C-020

### S-011 HTML report
- Tier: Sonnet
- Profile: software
- Depends on: S-009
- Inputs: src/renault_diag/report.py, D-011, D-016
- Actions:
  1. `mask_vin`: `None` → `unknown`; else `'*'*(len-4)+last4`.
  2. `render_html`: `<!doctype html>`, inline `<style>`, sections Adapter / Generic / ECUs / Warnings; every dynamic string through `html.escape(..., quote=True)`; descriptions shown next to matching codes.
  3. If `log_path`: read CSV, one inline `<svg>` polyline per numeric column (skip non-numeric), axis labels escaped. No `<script>`, no URLs.
- Outputs: src/renault_diag/report.py
- Evidence produced: T-U09, T-U09b, T-S05
- Done when: `pytest -q -k 'T_U09 or T_S05'` passes; CHK-02 still passes
- Checkpoint: append `S-011` to `.checkpoints/impl_state.json` `done`; commit `impl: S-011 HTML report`
- On failure: DR-09
- Gate: none
- Relevant decisions/claims: D-011, D-016, A-011

### S-012 CLI, full suite, audit
- Tier: Opus
- Profile: software
- Depends on: S-002..S-011
- Inputs: src/renault_diag/cli.py, D-### cli interface
- Actions:
  1. `argparse` with subcommands and exit codes per interface; `argparse` errors → return 2 (catch `SystemExit`).
  2. `check-adapter`: print `version: <v>` and `voltage: <v>` to stdout. `scan`: open `Elm327Transport` (unless `--generic-only`) → D-018 interlock (`01 0D` to `FUNCTIONAL_OBD`; speed > 0 → return 5) → `scan_all` (filtered by `--ecu`) → close; then, unless `--manufacturer-only`, `obd.OBD(port, fast=False, timeout=5)` → `read_generic` → close; warn if voltage < 12.0; write JSON atomically. No vehicle answer at all (generic not connected and every ECU absent) → 4.
  3. `clear-engine-codes`: build the D-### backup (transport only, see interface) and write it to `--backup-dir/pre-clear-<UTC timestamp>.json` first (adapter errors → 3); apply the D-018 interlock; print that clearing erases freeze-frame data and resets readiness monitors (an MOT/emissions test may fail until they complete); prompt `Type CLEAR ENGINE CODES to continue:`; exact match else return 5 without sending; on match send mode `04` to `FUNCTIONAL_OBD` with `allow_clear=True`.
  4. `log` without `--pids` uses defaults `RPM, SPEED, COOLANT_TEMP, ENGINE_LOAD, INTAKE_PRESSURE, MAF` intersected with the car's supported commands (dropped names printed as a warning); warn if adapter voltage < 12.0 V.
5. Map `AdapterNotFoundError/AdapterUnsupportedError` → 3, `ForbiddenRequestError` → 5, `KeyboardInterrupt` → 130, file/JSON errors → 2 (stderr message).
  6. Run `python -m pytest -q` → `119 passed`; `sha256sum -c tests/FROZEN_MANIFEST.sha256`; `pip-audit -r requirements.txt && pip-audit -r requirements-dev.txt`.
- Outputs: src/renault_diag/cli.py
- Evidence produced: T-I03, T-I04, T-O01, T-O02, T-S08, T-S09, T-P02 (+ all)
- Done when: `119 passed`, manifest OK, pip-audit clean (CHK-01); CHK-02 still passes
- Checkpoint: append `S-012` to `.checkpoints/impl_state.json` `done`; commit `impl: S-012 CLI, full suite, audit`
- On failure: DR-02, DR-05; failing frozen test → fix code, never test
- Gate: none
- Relevant decisions/claims: D-004, D-011, D-018, A-005, R-003, R-006, R-008

### S-013 Real-vehicle acceptance (human-executed)
- Tier: Sonnet
- Profile: software
- Depends on: S-012
- Inputs: plan/HARDWARE.md, HANDOFF.md §Real car
- Actions:
  1. Write `GATE-G-003.md` containing the human procedure: plug OBDLink EX into the centre-console socket, ignition ON engine OFF, run `renault-diag check-adapter --port <PORT>`, `renault-diag scan --port <PORT> --out scan.json --trace trace.log`, start engine, `renault-diag log --port <PORT> --out log.csv --duration 60`, `renault-diag report --scan scan.json --log log.csv --out report.html`.
  2. Include the DR-06/07/08 interpretation table and the question list from `plan/GATES.md`.
  3. Halt and wait.
- Outputs: GATE-G-003.md
- Evidence produced: none (acceptance evidence recorded by human)
- Done when: human reply recorded in `GATE-G-003.md`; CHK-02 still passes
- Checkpoint: append `S-013` to `.checkpoints/impl_state.json` `done`; commit `impl: S-013 Real-vehicle acceptance (human-executed)`
- On failure: Per G-003 response
- Gate: G-003
- Relevant decisions/claims: DR-06, DR-07, DR-08, C-014

### S-014 Merge to public main
- Tier: Haiku
- Profile: software
- Depends on: S-013 (G-003 = proceed)
- Inputs: implementation branch
- Actions:
  1. Write `GATE-G-002.md` (test log, manifest check, pip-audit output, `git diff --stat main...HEAD`). Halt.
  2. Only after `proceed`: `git checkout main && git merge --no-ff <impl-branch> && git push origin main`. Never tag, never publish to PyPI.
- Outputs: GATE-G-002.md; main branch
- Evidence produced: none
- Done when: human `proceed` recorded; push succeeded; CHK-02 still passes
- Checkpoint: append `S-014` to `.checkpoints/impl_state.json` `done`; commit `impl: S-014 Merge to public main`
- On failure: If push fails: retry 3× with backoff, else leave branch unmerged and report.
- Gate: G-002
- Relevant decisions/claims: A-008
