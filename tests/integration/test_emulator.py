# FROZEN — DO NOT MODIFY (see tests/FROZEN_MANIFEST.sha256, plan/DECISIONS.md)
import json
import socket

import pytest

from renault_diag.cli import main
from renault_diag.ecus import SCENIC3_ECUS
from renault_diag.generic import read_generic
from renault_diag.manufacturer import scan_all
from renault_diag.models import from_json
from renault_diag.transport import Elm327Transport
from tests.conftest import EXPECTED_ECM_KWP, EXPECTED_UCH_DTCS

pytestmark = pytest.mark.integration


def test_T_I01_generic_report(obd_conn):
    """T-I01 — generic EOBD read via python-OBD: VIN, MIL, readiness, protocol; SC-1; C-002; D-002."""
    g = read_generic(obd_conn)
    assert g.vin and len(g.vin) == 17
    assert g.mil_on is False and g.dtc_count == 0 and g.stored == []
    assert "15765" in g.protocol
    assert g.readiness and set(g.readiness.values()) <= {"complete", "incomplete", "unavailable"}
    assert "RPM" in g.supported


def test_T_I02_manufacturer_scan(emulator_port):
    """T-I02 — 9-ECU scan: UDS multi-frame, KWP fallback, session NRC tolerated, absent ECUs; SC-2; D-007/8/13."""
    with Elm327Transport(emulator_port, timeout_s=2) as t:
        res = {r.ecu: r for r in scan_all(t, SCENIC3_ECUS)}
    assert list(res) == [e.name for e in SCENIC3_ECUS]
    uch = res["UCH"]
    assert uch.present and uch.protocol == "uds" and uch.session_ok
    assert [(d.code, d.status) for d in uch.dtcs] == EXPECTED_UCH_DTCS
    ecm = res["ECM"]
    assert ecm.present and ecm.protocol == "kwp" and (ecm.kwp_dtc_count, ecm.kwp_raw) == EXPECTED_ECM_KWP
    air = res["AIRBAG"]
    assert air.present and not air.session_ok and air.protocol == "uds" and air.dtcs == []
    for name in ["ABS", "EPS", "TDB", "HVAC", "APB", "AT"]:
        assert res[name].present is False


def test_T_I03_cli_scan_and_report_end_to_end(emulator_port, tmp_path, monkeypatch):
    """T-I03 — CLI scan → JSON → report HTML, with all sockets forbidden (offline tool); SC-3, SC-4; A-011."""
    def no_net(*a, **k):
        raise AssertionError("network access attempted")
    monkeypatch.setattr(socket, "socket", no_net)
    out = tmp_path / "scan.json"
    assert main(["scan", "--port", emulator_port, "--out", str(out)]) == 0
    scan = from_json(out.read_text(encoding="utf-8"))
    assert scan.generic is not None and len(scan.ecus) == 9
    rep = tmp_path / "r.html"
    assert main(["report", "--scan", str(out), "--out", str(rep)]) == 0
    assert "B1007-41" in rep.read_text(encoding="utf-8")
    assert json.loads(out.read_text(encoding="utf-8"))["schema_version"] == 1


def test_T_I04_check_adapter_and_generic_only(emulator_port, tmp_path, capsys):
    """T-I04 — check-adapter prints version+voltage; --generic-only skips ECUs; SC-1."""
    assert main(["check-adapter", "--port", emulator_port]) == 0
    assert "ELM327" in capsys.readouterr().out
    out = tmp_path / "g.json"
    assert main(["scan", "--port", emulator_port, "--out", str(out), "--generic-only"]) == 0
    assert from_json(out.read_text(encoding="utf-8")).ecus == []
