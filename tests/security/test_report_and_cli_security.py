# FROZEN — DO NOT MODIFY (see tests/FROZEN_MANIFEST.sha256, plan/DECISIONS.md)
import pytest

from renault_diag.cli import main
from renault_diag.dtc import Dtc
from renault_diag.manufacturer import EcuResult
from renault_diag.models import ScanResult
from renault_diag.report import render_html

pytestmark = pytest.mark.security
EVIL = '<script>alert(1)</script><img src="https://evil.example/x">'


def test_T_S05_html_escapes_untrusted_strings(tmp_path):
    """T-S05 — ECU error text, adapter strings, descriptions and log headers are escaped; A-011; D-011."""
    scan = ScanResult("2026-09-24T12:00:00Z", "0.1.0", {"version": EVIL, "voltage_v": None}, None,
                      [EcuResult("UCH", True, "uds", True, [Dtc("B1007-41", 0x2F, "uds", "9007412F")], error=EVIL)],
                      [EVIL])
    log = tmp_path / "log.csv"
    log.write_text("timestamp_utc,elapsed_s,RPM" + "\n2026-09-24T12:00:00Z,0.0,800\n", encoding="utf-8")
    html = render_html(scan, log_path=log, descriptions={"B1007-41": EVIL})
    assert "<script" not in html.lower()
    assert "<img" not in html.lower()
    assert "evil.example" not in html or "&lt;img" in html


def test_T_S08_clear_requires_exact_phrase(tmp_path, fake_serial_factory, monkeypatch):
    """T-S08 — clear-engine-codes refuses without the exact typed phrase and sends no 04/14; SC-7; G-002; A-005."""
    import renault_diag.transport as tr
    make, holder = fake_serial_factory
    monkeypatch.setattr(tr.serial, "Serial", make({"03": "7E8 02 43 00"}))
    rc = main(["clear-engine-codes", "--port", "FAKE", "--backup-dir", str(tmp_path)],
              input_fn=lambda prompt="": "yes")
    assert rc == 5
    sent = holder["serial"].sent_commands() if "serial" in holder else []
    assert "04" not in sent and not any(c.startswith("14") for c in sent)
