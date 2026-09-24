# Hardware required

| Item | Recommendation | Why | Approx. cost |
|---|---|---|---|
| OBD adapter | **OBDLink EX** (USB, STN2230, FTDI driver) | Listed as "tested and confirmed" by DDT4all for Renault CAN ECUs; all OBD-II protocols (C-016, C-017) | ~£65 |
| Alternative | OBDLink MX+ (Bluetooth) | Same STN family; Bluetooth adds dropout risk (DDT4all README) | ~£100–120 |
| Avoid | Generic "ELM327 v1.5" clones | Often cannot address Renault CAN modules; clones are limited to v1.4-level functions (C-016); the tool's self-test (D-014) rejects adapters without `ATCRA` | — |
| Computer | Laptop, Windows 10/11 or Linux, Python 3.12, one free USB port | Runs the CLI | — |
| Vehicle power | Healthy 12 V battery (≥ 12.2 V engine off); charger/maintainer for sessions > 15 min with ignition on | Long ignition-on sessions drain the battery; tool prints adapter voltage | optional |

**Socket location (Scénic III, 2009–2016):** centre console between the front seats — behind/under the cup holder, or under the armrest cover on armrest trims (C-005). Scénic IV: under the steering wheel, left of the pedals.

**Linux:** adapter appears as `/dev/ttyUSB0` (FTDI); add user to `dialout`. **Windows:** install FTDI VCP driver; adapter appears as `COMn`.
