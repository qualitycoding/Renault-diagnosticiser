"""Mechanical consistency check (Phase 3.6 step 2 / Phase 5.1): every referenced ID is defined,
every test ID in TRACEABILITY exists in tests/, every referenced repo path exists, no N/A artifact required."""
import json, pathlib, re, subprocess, sys
R = pathlib.Path(__file__).resolve().parents[2]
txt = {p: p.read_text(encoding="utf-8") for p in R.rglob("*.md") if ".git" not in p.parts}
paths_txt = "\n".join(v for k, v in txt.items() if k.name != "PROFILE.md")
allt = "\n".join(txt.values())
problems = []
defined = {
 "D": set(re.findall(r"\| (D-\d{3}) \|", (R/"plan/DECISIONS.md").read_text())),
 "A": set(re.findall(r"\| (A-\d{3}) \|", (R/"plan/ASSUMPTIONS.md").read_text())),
 "C": {c["id"] for c in json.load(open(R/"research/claims.json"))},
 "S": set(re.findall(r"### (S-\d{3})", (R/"plan/PLAN.md").read_text())),
 "G": set(re.findall(r"\| (G-\d{3}) \|", (R/"plan/GATES.md").read_text())),
 "DR": set(re.findall(r"\| (DR-\d{2}) \|", (R/"plan/DECISIONS.md").read_text())),
}
rr = R/"premortem/RISK_REGISTER.md"
defined["R"] = set(re.findall(r"\| (R-\d{3}) \|", rr.read_text())) if rr.exists() else set()
test_src = "\n".join(p.read_text() for p in (R/"tests").rglob("*.py"))
tids = set(re.findall(r"T-[USIOP]\d{2}[a-d]?", test_src))
for kind, pat in [("D", r"D-\d{3}"), ("A", r"A-\d{3}"), ("C", r"C-\d{3}"), ("S", r"S-\d{3}"), ("G", r"G-\d{3}"), ("DR", r"DR-\d{2}"), ("R", r"R-\d{3}")]:
    for ref in sorted(set(re.findall(r"(?<![\w.])" + pat + r"(?!\d)", allt))):
        if ref not in defined[kind] and not (kind == "G" and ref == "G-001"):
            problems.append(f"undefined {ref}")
for ref in sorted(set(re.findall(r"T-[USIOP]\d{2}[a-d]?", allt))):
    if ref not in tids:
        problems.append(f"test id {ref} referenced but not in tests/")
for t in sorted(tids):
    if t not in (R/"plan/TRACEABILITY.md").read_text() and t.rstrip("abcd") not in (R/"plan/TRACEABILITY.md").read_text():
        problems.append(f"test {t} missing from TRACEABILITY")
created_by_steps = {"GATE-G-002.md", "GATE-G-003.md", "DEVIATIONS.md", "BLOCKED.md", "TEST_CHALLENGE.md", ".checkpoints/impl_state.json",
                    "scan.json", "log.csv", "report.html", "trace.log", ".venv/", "d.csv", "r.html", "p.csv"}
for ref in sorted(set(re.findall(r"`((?:plan|research|tests|src|premortem|\.checkpoints)/[\w./-]+)`", paths_txt))):
    if not (R/ref).exists() and ref not in created_by_steps:
        problems.append(f"missing path {ref}")
for na in ["math/", "figures/SPEC.md", "manuscript/", "plan/OPERATIONS.md", "research/NOVELTY.md"]:
    if re.search(r"(?<!N/A\) and produce no artifacts:)\b" + re.escape(na), (R/"plan/PLAN.md").read_text() + (R/"HANDOFF.md").read_text()):
        problems.append(f"N/A artifact referenced as required: {na}")
m = subprocess.run(["sha256sum", "-c", "--quiet", "tests/FROZEN_MANIFEST.sha256"], cwd=R, capture_output=True, text=True)
if m.returncode: problems.append("freeze manifest mismatch: " + m.stdout + m.stderr)
print("\n".join(problems) or "OK: 0 items")
sys.exit(1 if problems else 0)
