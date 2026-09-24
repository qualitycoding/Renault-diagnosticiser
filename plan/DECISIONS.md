# Decisions, Interfaces & Decision Rules (D-###)

## Architecture decisions
| ID | Decision | Rationale / claims |
|---|---|---|
| D-001 | Python 3.12 package `renault_diag` under `src/`, CLI entry point `renault-diag`. | A-006 |
| D-002 | Generic OBD-II/EOBD uses python-OBD 0.7.3 (pinned). Our code never re-implements generic PID decoding. | C-001, C-002, C-003 |
| D-003 | Manufacturer ECU access uses our own thin ELM327 transport over pyserial (python-OBD cannot switch CAN headers per request). | C-011 |
| D-004 | **Safety allowlist.** Every payload passes `safety.check_request` and every AT/ST command passes `safety.check_at_command` *before* any byte is written. Allowed payloads: OBD modes `01 02 03 06 07 09 0A`; `10 C0`, `10 01`, `10 81`; `3E xx` (len ≤ 2); `17 ...`; `18 ...`; `19 01/02/0A ...`; `1A ...`; `21 ...`; `22 ...`. Mode `04` and service `14` are allowed **only** when `allow_clear=True` and the target is the ECM (`7E0`) or functional OBD (`7DF`). Everything else is forbidden, including `11 12 23 27 28 2E 2F 30 31 34 35 36 37 3B 3D 85`. Allowed AT commands (after removing spaces, case-insensitive): `Z WS D E0 E1 L0 L1 S0 S1 H0 H1 AL CAF0 CAF1 CFC1 SP6 SP0 DP DPN RV I @1 AT0 AT1 AT2`, and the prefixed forms `SH<hex3>`, `CRA<hex3>`, `CRA` (reset), `FCSH<hex3>`, `FCSD300000`, `FCSM1`, `ST<hex2>`. Every `ST…` (STN extension) command and every other AT command is forbidden, notably `PP…` (writes adapter EEPROM), `@3`, `MA`, `BRD`. | C-018 (narrowed), A-005 |
| D-005 | Transport configuration: `ATZ, ATE0, ATL0, ATS1, ATH1, ATSP6, ATAL, ATCAF1, ATCFC1`; per-ECU: `ATSH<tx>, ATCRA<rx>, ATFCSH<tx>, ATFCSD300000, ATFCSM1`; header commands are re-sent only when the target ECU changes. 11-bit CAN 500 kbit/s only (protocol 6). | C-004, C-011, C-024 |
| D-006 | ECU table `SCENIC3_ECUS` (order fixed): ECM 7E0/7E8, ABS 740/760, EPS 742/762, TDB 743/763, HVAC 744/764, UCH 745/765, AIRBAG 752/772, APB 755/775, AT 7E1/7E9. Functional OBD: 7DF/7E8. | C-006, C-008 |
| D-007 | Open session `10 C0` first. NRC → record `session_ok=false` and continue in default session. `NoResponseError` → ECU `present=false`, stop that ECU. | C-012 |
| D-008 | DTC read order: UDS `19 02 AF` first; if NRC `0x11` or `0x12`, fall back to KWP `17 FF 00`. Mask `AF` is used for every adapter (as DDT4all does for plain ELM). | C-007, C-023 |
| D-009 | UDS DTCs decoded fully (3-byte code → `L####-FF` text, 8 status flags). All-zero records and trailing zero padding are ignored. KWP DTCs: report count + raw hex only. | C-013, C-019, C-022 |
| D-010 | Renault text descriptions only from an optional user CSV (`code,description`); none shipped. | C-009 |
| D-011 | "Dashboard" = one self-contained HTML file (inline CSS + inline SVG charts, no JS, no external URLs). No listening socket anywhere. | A-006, A-011 |
| D-012 | Tests use ELM327-emulator 4.0.0 **in-process** (`Elm(batch_mode=True)`, `get_pty()`, `run` in a daemon thread) with a custom scenario built in `tests/conftest.py`; multi-frame replies are verbatim frame lines via `ST()`. Emulator is dev-only; never vendored. | C-010, C-015, C-026 |
| D-013 | A scan never aborts because one ECU fails; per-ECU errors are recorded. Only loss of the serial port aborts. | R3 round 1 |
| D-014 | `open()` performs an adapter self-test: `ATI` must contain `ELM327` or `STN`/`OBDLink`, and `ATCRA7E8` must return `OK`; otherwise `AdapterUnsupportedError`. | C-016 |
| D-015 | Dependencies hash-pinned; `pip-audit` must be clean before any merge. | C-021, C-025 |
| D-017 | VIN is decoded from the raw python-OBD message bytes (`bytes(resp.messages[0].data)[3:20]`, ASCII, non-alphanumerics stripped), not from `resp.value`, because python-OBD 0.7.3 truncates it (C-027). |
| D-018 | **Moving-vehicle interlock.** Before any manufacturer-ECU request, `scan` sends OBD `01 0D` to `FUNCTIONAL_OBD` through the transport. Speed > 0 → stop with exit 5 and message `vehicle must be stationary`, sending nothing further. `NoResponseError` → continue with a warning. `clear-engine-codes` applies the same interlock. | R-003, A-018 |
| D-016 | VIN masked in HTML (`*` except last 4) unless `--show-vin`; full VIN only in local JSON. | A-012 |

## Public interfaces (stubs committed in `src/renault_diag/`)
All signatures below are binding; the stubs raise `NotImplementedError`.

### `errors.py` (implemented, not a stub)
`DiagError(Exception)`; subclasses `AdapterNotFoundError`, `AdapterUnsupportedError`, `NoResponseError`, `BusError`, `BufferFullError`, `ProtocolError`, `ForbiddenRequestError`, `NegativeResponseError(service:int, nrc:int)` (attributes `.service`, `.nrc`).

### `ecus.py` (partially stubbed)
`EcuDef(name:str, label:str, tx_id:int, rx_id:int)` frozen dataclass (final); `SCENIC3_ECUS: tuple[EcuDef, ...]` (stub is empty; implementer fills per D-006); `FUNCTIONAL_OBD: EcuDef` (final); `ecu_by_name(name:str) -> EcuDef` (case-insensitive; unknown → `ValueError`; stub raises `NotImplementedError`).

### `safety.py`
`check_request(payload: bytes, *, target: EcuDef, allow_clear: bool = False) -> None` — raises `ForbiddenRequestError`.
`check_at_command(cmd: str) -> None` — `cmd` given without the leading `AT` for AT commands (e.g. `"SH745"`), or starting with `ST` for STN commands; raises `ForbiddenRequestError`.

### `elm_parse.py`
`parse_response(text: str, rx_id: int) -> bytes` — `text` = raw adapter output up to (excluding) `>`; lines separated by `\r`/`\n`; header display on, spaces on or off. Returns reassembled ISO-TP payload (PCI removed, padding removed per length). Ignores echo, `SEARCHING...`, blank lines, frames from other IDs. `NO DATA` → `NoResponseError`; `CAN ERROR`, `BUS ERROR`, `BUS INIT...ERROR`, `UNABLE TO CONNECT` → `BusError`; `BUFFER FULL` anywhere → `BufferFullError`; `?` → `ProtocolError`; bad CF sequence / length mismatch / no frames from `rx_id` → `ProtocolError`. If several complete messages from `rx_id` are present, response-pending messages (`7F xx 78`) are discarded and the **last** remaining message is returned; if only response-pending messages are present, that `7F xx 78` payload is returned (the transport then reads again).

### `dtc.py`
`Dtc(code:str, status:int|None, source:str, raw:str)` frozen dataclass (`source` ∈ `obd|uds|kwp`; `raw` = uppercase hex of the record bytes).
Code text: `decode_obd_pair` → letter from bits 7–6 of `b0` (`00`P `01`C `10`B `11`U), digit from bits 5–4, hex of the low nibble of `b0`, then `b1` as two uppercase hex digits (e.g. `0x90,0x07` → `B1007`); `(0,0)` → `None`. UDS code = pair text + `-` + failure-type byte as two hex digits (e.g. `90 07 41` → `B1007-41`).
`decode_obd_pair(b0:int, b1:int) -> str|None`; `decode_uds_19_02(payload: bytes) -> tuple[int, list[Dtc]]`; `decode_kwp_17(payload: bytes) -> tuple[int, str]` (count, raw hex of records); `status_flags(status:int) -> list[str]` (ISO 14229 bit names, bit0→`testFailed` … bit7→`warningIndicatorRequested`); `load_descriptions(path) -> dict[str,str]` (UTF-8 CSV, header `code,description`, ≤ 10 000 rows, code regex `^[PCBU][0-9A-F]{4}(-[0-9A-F]{2})?$`, description ≤ 200 chars, else `ValueError` naming the line).

### `transport.py`
`AdapterInfo(version:str, voltage_v:float|None)`.
`Elm327Transport(port:str, baudrate:int=38400, timeout_s:float=5.0, serial_factory=None, trace_path=None)` (`serial_factory=None` → `serial.Serial` resolved at `open()` time) — context manager; `open() -> AdapterInfo`; `close()`; `at(cmd:str) -> str`; `read_voltage() -> float|None`; `request(ecu:EcuDef, payload:bytes, *, allow_clear:bool=False) -> bytes` (returns positive response payload; NRC → `NegativeResponseError`; NRC `0x78` with no final answer before the prompt → re-send the same (already allowlisted, read-only) request, max 10 times, then `NoResponseError`; wrong response SID → `ProtocolError`); serial open failure → `AdapterNotFoundError`.

### `generic.py`
`GenericReport(vin, mil_on, dtc_count, stored:list[Dtc], pending:list[Dtc], readiness:dict[str,str], protocol:str, supported:list[str])`; `read_generic(conn: obd.OBD) -> GenericReport`.

### `manufacturer.py`
`EcuResult(ecu:str, present:bool, protocol:str|None, session_ok:bool, dtcs:list[Dtc], kwp_dtc_count:int|None, kwp_raw:str|None, error:str|None)`; `scan_ecu(t, ecu) -> EcuResult`; `scan_all(t, ecus=SCENIC3_ECUS) -> list[EcuResult]`.

### `models.py`
`ScanResult(created_utc:str, tool_version:str, adapter:dict, generic:GenericReport|None, ecus:list[EcuResult], warnings:list[str], schema_version:int=1)`; `to_json(r)->str`; `from_json(s)->ScanResult` (exact round-trip); `write_json_atomic(path, r)` (temp file + `os.replace`).

### `logger.py`
`LogSummary(samples:int, path:str, resumed:bool, stopped_by:str)`; `log_live(conn, pids:list[str], out_path, *, interval_s=0.5, max_samples=None, max_duration_s=None, stop_event=None, sleep=time.sleep) -> LogSummary`. CSV header `timestamp_utc,elapsed_s,<PID>…`; existing file with identical header → append (`resumed=True`); different header → `ValueError`, file untouched; each row flushed; `KeyboardInterrupt`/`stop_event` → clean stop (`stopped_by` ∈ `max_samples|max_duration|stop_event|interrupt`); unsupported PID names → `ValueError` before the file is opened.

### `report.py`
`mask_vin(vin:str|None) -> str`; `render_html(scan, log_path=None, *, show_vin=False, descriptions=None) -> str`.

### `cli.py`
`main(argv:list[str]|None=None, *, input_fn=input) -> int`. Subcommands: `ports`; `check-adapter --port`; `scan --port --out [--generic-only | --manufacturer-only] [--ecu NAME]… [--trace FILE]` (`--trace` appends every line sent to and received from the adapter, prefixed `>> ` / `<< `, for G-003 evidence); `log --port --out [--pids …] [--interval] [--duration]`; `report --scan --out [--log] [--show-vin] [--descriptions]`; `clear-engine-codes --port --backup-dir` (backup = `ScanResult` with `generic=None`, `ecus=[scan_ecu(ECM)]`, and the raw hex of a mode `03` request to `FUNCTIONAL_OBD` appended to `warnings`; all through `Elm327Transport`, never python-OBD); `check-adapter` prints `version: …` and `voltage: …` lines to stdout. Exit codes: 0 OK; 2 usage/config/file error; 3 adapter not found/unsupported; 4 no vehicle response (speed probe unanswered **and** every attempted ECU absent **and** generic read not connected or not attempted); 5 refused (safety or confirmation); 130 interrupted. `clear-engine-codes` first writes a scan JSON into `--backup-dir`, then requires the exact line `CLEAR ENGINE CODES` from `input_fn`; there is no bypass flag.

## Decision rules (if → then)
| # | If | Then |
|---|---|---|
| DR-01 | A dependency install fails with `--require-hashes` | Do not relax hashes. Re-run `pip-compile` for that file only with the same pins; if the pinned version is gone from PyPI, halt and write `BLOCKED.md`. |
| DR-02 | `pip-audit` reports a vulnerability | Bump only the affected package to the lowest fixed version, re-lock, re-run the full suite; if no fix exists, halt `BLOCKED.md` (security). |
| DR-03 | python-OBD returns an unexpected shape (e.g. `value` type differs) | Adapt `generic.py` conversion; never modify frozen tests; if a frozen test encodes the shape, write `TEST_CHALLENGE.md`. |
| DR-04 | Emulator behaves differently from D-012 (e.g. API rename) | Only `tests/conftest.py` would need change → it is frozen → write `TEST_CHALLENGE.md` and halt. |
| DR-05 | Performance test T-P01/T-P02 misses target | Profile (`python -m cProfile`), remove overhead in our code; do not change interval defaults or tests; after 3 attempts halt `BLOCKED.md`. |
| DR-06 | Real car (G-003): an ECU in D-006 does not answer | Record in `GATE-G-003.md`; it is not a failure (D-013). |
| DR-07 | Real car: every manufacturer ECU returns `CAN ERROR` but generic OBD works | Record; hypothesis = adapter/clone limitation (C-016); human decides at G-003. |
| DR-08 | Real car: any request not in the D-004 allowlist appears in the raw log | Stop immediately; this is a Critical defect; halt `BLOCKED.md`. |
| DR-09 | Any unanticipated situation | Choose the most reversible option that does not expand scope, log it in `DEVIATIONS.md` with rationale, and continue — **unless** it touches frozen tests, security, data integrity, a public interface, research integrity, or (upward) a statement's evidence class, in which case halt and write `BLOCKED.md`. |
