# Research Round 2 (2026-09-24)

**R2 Breadth (new leaves Q3.1–Q3.3):** ELM327-emulator 4.0.0 found; custom scenario support confirmed in spike S3 (C-010). Licence checked: CC-BY-NC-SA-4.0 (C-015) → D-012 restricts it to dev/test, never vendored.

**R3 Synthesis:** DTC formats: UDS 0x19 02 (C-013) vs KWP 17 FF 00 (C-022: layouts vary per ECU) → D-009: decode UDS fully; show KWP as count + raw hex only.

**R4 Depth:** C-013 checked against udsoncan source (Tier 1). Scénic IV comparison scripted:

```
python3 -c "import json;P=json.load(open('src/ddt4all/resources/projects.json'))['projects'];v=P['[XFA] - Renault Scenic IV'];w=P['[X95] - Renault Megane III'];print([a for a in ['7A','01','26','2C','51','29','6E','0D','04'] if (v['snat'].get(a),v['dnat'].get(a))!=(w['snat'].get(a),w['dnat'].get(a))])"
# output: []
```
→ C-008 verified.

**R5 Adversarial:** Attempted to break the emulator-as-oracle assumption: the emulator is not a real ECU, so a test passing on it does not prove car behaviour → mitigated by gate G-003 (human in-car acceptance with captured raw logs) and by fixtures built from DDT4all's own recorded response vectors (C-022).

**R6 Empirical:** spike S3 (custom Renault scenario), spike S4 (throughput → A-016).

New load-bearing claims: 3 (C-010, C-015, C-020). Continue.
