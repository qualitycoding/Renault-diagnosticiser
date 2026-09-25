# renault-diag

Read-only OBD-II/EOBD and Renault ECU fault-code reader for a 2016 Renault Scenic III.

> **Status:** planning is finished and the test suite is written, but most modules in `src/renault_diag/` are still stubs. The commands below describe the planned interface (`plan/DECISIONS.md`).

## What it does

`renault-diag` is a Python command-line tool that talks to the car through a USB ELM327-compatible adapter (an OBDLink EX is recommended; see `plan/HARDWARE.md`). It can:

- **Read generic EOBD data:** VIN, check-engine lamp (MIL) status, stored and pending fault codes, readiness monitors, and supported PIDs.
- **Scan Renault ECUs for fault codes:** engine (ECM), ABS, power steering, instrument cluster, climate control, body control (UCH), airbag, electronic parking brake, and automatic gearbox. It tries UDS first and falls back to KWP2000. If one ECU fails, the scan records the error and moves on.
- **Log live data to CSV:** selected PIDs at a fixed interval. It can resume an existing log file.
- **Build an HTML report:** one self-contained file made from a scan and an optional log. The VIN is masked unless you pass `--show-vin`.
- **Clear engine codes (optional):** only on the engine ECU. It saves a backup scan first and requires you to type `CLEAR ENGINE CODES` to confirm.

### Safety

The tool is meant to never change anything on the car. Every request to an ECU and every adapter command is checked against a fixed allowlist before any bytes are sent. Writes, security access, routine control, flashing, and commands that change adapter settings are all blocked. Before it contacts any Renault ECU, the tool asks the car for its speed and stops if the car is moving.

### Commands

```bash
renault-diag ports                                       # list serial ports
renault-diag check-adapter --port COM3                   # adapter version and battery voltage
renault-diag scan --port COM3 --out scan.json            # generic + Renault ECU fault codes
renault-diag log --port COM3 --out log.csv --duration 60 # live data
renault-diag report --scan scan.json --log log.csv --out report.html
renault-diag clear-engine-codes --port COM3 --backup-dir backups/
```

Before a scan, turn the ignition on, leave the engine off, and make sure the car is stationary with the parking brake on. The ABS warning lamp may flash while the ABS module is being read. It should go out after the session or the next ignition cycle.

## License

Licensed under the [Apache License, Version 2.0](LICENSE).

This project depends on [python-OBD](https://github.com/brendan-w/python-OBD), which is licensed under GPL-2.0-or-later. It is installed as a separate dependency and is not included in this repository. If you distribute a bundle or binary that includes python-OBD, that bundle as a whole is subject to the GPL.
