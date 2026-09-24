# Research Round 3 (2026-09-24) — saturation check

**R2/R3:** No new leaves. Re-checked every load-bearing claim's confidence: all `verified` or `corroborated` (18 load-bearing; see `claims.json`). No contradictions between sources.

**R4 Depth:** C-024 (ELM terminal responses) confirmed from datasheet + kernel driver docs.

**R5 Adversarial:** searched for breaking changes: python-OBD 0.7.3 is the latest (2025-04); ELM327-emulator 4.0.0 is one week old (2026-09-17) → pinned exactly; its CLI `-b FILE` batch mode behaves differently from older docs (spike S1 first attempt failed until the port was read from the batch file) — recorded in D-012 so the implementer uses the in-process API instead.

**R6 Empirical — environment (C-025):**
```
python3 -m venv tools && . tools/bin/activate && pip install pip-tools==7.5.1 pip-audit==2.10.1
pip-compile --generate-hashes --strip-extras --allow-unsafe -o requirements.txt requirements.in
pip-compile --generate-hashes --strip-extras --allow-unsafe -o requirements-dev.txt requirements-dev.in
python3 -m venv verifyenv && . verifyenv/bin/activate && pip install --require-hashes -r requirements.txt -r requirements-dev.txt   # rc=0
pip-audit -r requirements.txt ; pip-audit -r requirements-dev.txt   # "No known vulnerabilities found" x2
```

**Termination:** 3 rounds complete; round 3 produced no new load-bearing claims, no downgrades, no unresolved contradictions → **saturated**. Non-load-bearing single-source claims (C-007, C-012, C-014, C-022) are carried as risks R-004/R-005 in Phase 4.

**Addendum (same round, R6):**
- pip-audit flagged `setuptools==80.9.0` (PYSEC-2026-3447, fixed in 83.0.0) when it was first added as a build dependency → pinned `setuptools==84.0.0`; re-audit clean. This is exactly the decision rule D-015 in action.
- Spike S6 (multi-frame on a custom header) found emulator limitation C-026 → fixtures must supply verbatim ISO-TP frame lines via `ST()`. Not a new external claim about cars; it changes test construction only (D-012). Saturation criterion still met: no confidence downgrades, no contradictions.
