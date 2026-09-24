# Human Gates

At a gate the implementer halts, writes `GATE-<id>.md` with the evidence bundle, and waits. Allowed responses: `proceed`, `proceed-with-rescope: <text>`, `stop`.

| Gate | Trigger step | Evidence bundle | Questions for the human | Branches |
|---|---|---|---|---|
| G-001 | — | N/A (`math`/`computational` inactive) | — | — |
| G-002 | S-014 (before merging to public `main`) **and** before any `clear-engine-codes` run on the real car | Full test log, `pip-audit` output, `sha256sum -c tests/FROZEN_MANIFEST.sha256` output, diff summary; for clearing: the pre-clear backup JSON | "Merge to public main?" / "Clear the listed engine codes on the real car?" | `proceed` → merge / human runs clear; `stop` → leave branch unmerged / do not clear; `rescope` → apply text then re-run S-012 |
| G-003 | S-013 (first real-vehicle session, performed by the human) | Human-captured `check-adapter` output, `scan.json`, raw adapter log (`--trace` file), 60 s `log` CSV, HTML report | "Did any ECU misbehave or any warning lamp change? Which ECUs answered? Is the data plausible?" | `proceed` → S-014; `rescope` → e.g. edit ECU table, back to S-005 with a TEST_CHALLENGE; `stop` → halt |

The implementer (an AI agent) never connects to the real vehicle itself; G-003 is executed by the human with the commands in `HANDOFF.md`.
