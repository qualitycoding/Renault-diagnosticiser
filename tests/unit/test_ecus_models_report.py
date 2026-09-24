# FROZEN — DO NOT MODIFY (see tests/FROZEN_MANIFEST.sha256, plan/DECISIONS.md)
import json
import os

import pytest

from renault_diag.dtc import Dtc
from renault_diag.ecus import SCENIC3_ECUS, ecu_by_name
from renault_diag.generic import GenericReport
from renault_diag.manufacturer import EcuResult
from renault_diag.models import ScanResult, from_json, to_json, write_json_atomic
from renault_diag.report import mask_vin, render_html

pytestmark = pytest.mark.unit


def test_T_U05_ecu_table():
    """T-U05 — exact ECU table; SC-2; C-006; D-006."""
    assert [(e.name, e.tx_id, e.rx_id) for e in SCENIC3_ECUS] == [
        ("ECM", 0x7E0, 0x7E8), ("ABS", 0x740, 0x760), ("EPS", 0x742, 0x762), ("TDB", 0x743, 0x763),
        ("HVAC", 0x744, 0x764), ("UCH", 0x745, 0x765), ("AIRBAG", 0x752, 0x772), ("APB", 0x755, 0x775),
        ("AT", 0x7E1, 0x7E9)]
    assert ecu_by_name("uch").tx_id == 0x745
    assert ecu_by_name("OBD").tx_id == 0x7DF
    with pytest.raises(ValueError):
        ecu_by_name("NOPE")


def sample_scan():
    g = GenericReport(vin="VF1JZ000000000001", mil_on=True, dtc_count=1,
                      stored=[Dtc("P0133", None, "obd", "0133")], pending=[],
                      readiness={"Catalyst": "unavailable", "EGR": "complete"},
                      protocol="ISO 15765-4 (CAN 11/500)", supported=["RPM", "SPEED"])
    e = [EcuResult("UCH", True, "uds", True, [Dtc("B1007-41", 0x2F, "uds", "9007412F")]),
         EcuResult("ABS", False, error="no response")]
    return ScanResult("2026-09-24T12:00:00Z", "0.1.0", {"version": "ELM327 v1.5", "voltage_v": 12.6}, g, e, ["w1"])


def test_T_U08_json_round_trip_and_atomic(tmp_path):
    """T-U08 — exact JSON round trip, schema_version, atomic write; SC-3; D-### models."""
    s = sample_scan()
    txt = to_json(s)
    assert json.loads(txt)["schema_version"] == 1
    assert from_json(txt) == s
    p = tmp_path / "scan.json"
    write_json_atomic(p, s)
    assert from_json(p.read_text(encoding="utf-8")) == s
    assert [f for f in os.listdir(tmp_path) if f != "scan.json"] == []


def test_T_U09_report_content():
    """T-U09 — self-contained HTML, masked VIN, lists ECUs and codes; SC-4; D-011, D-016."""
    html = render_html(sample_scan())
    assert html.lstrip().lower().startswith("<!doctype html>")
    assert "VF1JZ000000000001" not in html and "0001" in html
    for needle in ["UCH", "B1007-41", "P0133", "ABS", "no response"]:
        assert needle in html
    assert "http://" not in html and "https://" not in html and "<script" not in html.lower()
    assert "VF1JZ000000000001" in render_html(sample_scan(), show_vin=True)
    assert mask_vin("VF1JZ000000000001") == "*************0001"
    assert mask_vin(None) == "unknown"


def test_T_U09b_report_with_log_has_svg(tmp_path):
    """T-U09b — logged columns rendered as inline SVG; SC-5; D-011."""
    log = tmp_path / "log.csv"
    log.write_text("timestamp_utc,elapsed_s,RPM\n2026-09-24T12:00:00Z,0.0,800\n2026-09-24T12:00:01Z,1.0,900\n",
                   encoding="utf-8")
    html = render_html(sample_scan(), log_path=log)
    assert "<svg" in html and "RPM" in html
