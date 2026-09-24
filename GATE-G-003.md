# GATE G-003 — Real-vehicle acceptance

**Status: WAITING** — this step is executed by the human, not the implementer. The implementer has never connected to a real vehicle.

## Preconditions
- Vehicle stationary, parking brake on.
- Ignition ON, engine OFF for the scan; engine running only for the live log.
- OBDLink EX (or MX+) plugged into the diagnostic socket: centre console between the front seats on a Scénic III (behind/under the cup holder, or under the armrest cover); under the steering wheel on a Scénic IV (`plan/HARDWARE.md`).
- Environment set up per `plan/ENVIRONMENT.md`, `pip-audit` clean, `sha256sum -c tests/FROZEN_MANIFEST.sha256` all `OK`, `pytest -q` → `119 passed` (all true as of commit `91f9957`).

## Procedure
```bash
. .venv/bin/activate
renault-diag ports
renault-diag check-adapter --port /dev/ttyUSB0          # Windows: COM3 etc.
renault-diag scan --port /dev/ttyUSB0 --out scan.json --trace trace.log
# now start the engine
renault-diag log --port /dev/ttyUSB0 --out log.csv --duration 60
renault-diag report --scan scan.json --log log.csv --out report.html
```
Open `report.html` in a browser and read it.

## Evidence to record here (paste below)
1. `check-adapter` output (version, voltage).
2. `scan.json` contents (or a summary: which of the 9 ECUs answered, protocol, DTC codes found).
3. `trace.log` — **required**. Per DR-08, every line must match the D-004 allowlist; if anything outside it appears, stop immediately and report it as Critical.
4. `log.csv` — first and last few rows, and the row count.
5. Anything unusual: warning lamps changing state, error messages, the tool hanging.

## Questions (answer each)
- Did any ECU misbehave, or did any warning lamp change state during or after the session? (ABS/ESP lamp flashing during the ABS read and clearing after ignition-cycle is expected per C-014 — did that happen, or something else?)
- Which of the 9 ECUs (ECM, ABS, EPS, TDB, HVAC, UCH, AIRBAG, APB, AT) answered as present? Does that match what a professional Renault scan tool would report, if you have one to compare against?
- Is the live-logged data (RPM, speed, coolant temp, etc.) plausible?
- Did `renault-diag` ever hang, crash, or print something surprising?

## Response
Reply with one of:
- `proceed` — evidence looks correct, continue to S-014 (G-002 merge gate).
- `proceed-with-rescope: <text>` — e.g. an ECU address is wrong, a decode looks off. I'll fix it, add a `TEST_CHALLENGE.md` if it means changing a frozen test, and come back to this gate.
- `stop` — do not proceed.
