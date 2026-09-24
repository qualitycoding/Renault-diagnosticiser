# FROZEN — DO NOT MODIFY (see tests/FROZEN_MANIFEST.sha256, plan/DECISIONS.md)
import threading

import pytest

from renault_diag.cli import main
from renault_diag.ecus import EcuDef
from renault_diag.errors import AdapterNotFoundError, BusError
from renault_diag.logger import log_live
from renault_diag.manufacturer import scan_all
from renault_diag.models import write_json_atomic

pytestmark = pytest.mark.operational


class FakeResp:
    def __init__(self, v):
        self.value = v

    def is_null(self):
        return self.value is None


class FakeConn:
    """Minimal python-OBD-like connection: supported_commands contain objects with .name."""

    class Cmd:
        def __init__(self, n):
            self.name = n

    def __init__(self, names=("RPM", "SPEED"), fail_at=None):
        self.supported_commands = {self.Cmd(n) for n in names}
        self.calls = 0
        self.fail_at = fail_at

    def query(self, cmd, force=False):
        self.calls += 1
        if self.fail_at and self.calls >= self.fail_at:
            raise KeyboardInterrupt
        return FakeResp(float(self.calls))


def test_T_O01_bad_port_exit_code(capsys):
    """T-O01 — unopenable port → exit 3 with a human message; SC-8."""
    assert main(["check-adapter", "--port", "/dev/definitely-not-here"]) == 3
    assert capsys.readouterr().err.strip() != ""


def test_T_O02_config_errors(tmp_path):
    """T-O02 — usage errors, missing and malformed scan files → exit 2; SC-8."""
    assert main([]) == 2
    assert main(["report", "--scan", str(tmp_path / "missing.json"), "--out", str(tmp_path / "r.html")]) == 2
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    assert main(["report", "--scan", str(bad), "--out", str(tmp_path / "r.html")]) == 2
    assert not (tmp_path / "r.html").exists()


def test_T_O03_logger_resume(tmp_path):
    """T-O03 — second run appends to identical-header file; header written once; SC-5."""
    p = tmp_path / "log.csv"
    s1 = log_live(FakeConn(), ["RPM", "SPEED"], p, interval_s=0, max_samples=5, sleep=lambda s: None)
    s2 = log_live(FakeConn(), ["RPM", "SPEED"], p, interval_s=0, max_samples=5, sleep=lambda s: None)
    lines = p.read_text(encoding="utf-8").splitlines()
    assert (s1.resumed, s2.resumed, s2.stopped_by) == (False, True, "max_samples")
    assert lines[0] == "timestamp_utc,elapsed_s,RPM,SPEED" and len(lines) == 11
    assert sum(1 for ln in lines if ln.startswith("timestamp_utc")) == 1


def test_T_O04_logger_header_mismatch_and_unsupported(tmp_path):
    """T-O04 — different header → ValueError, file untouched; unsupported PID → ValueError before file creation."""
    p = tmp_path / "log.csv"
    p.write_text("timestamp_utc,elapsed_s,RPM\nx,0,1\n", encoding="utf-8")
    before = p.read_bytes()
    with pytest.raises(ValueError):
        log_live(FakeConn(), ["RPM", "SPEED"], p, interval_s=0, max_samples=1, sleep=lambda s: None)
    assert p.read_bytes() == before
    q = tmp_path / "new.csv"
    with pytest.raises(ValueError):
        log_live(FakeConn(), ["NOT_A_PID"], q, interval_s=0, max_samples=1, sleep=lambda s: None)
    assert not q.exists()


def test_T_O05_logger_interrupt_and_stop_event(tmp_path):
    """T-O05 — Ctrl-C mid-run keeps complete rows; stop_event stops cleanly; SC-5, SC-8."""
    p = tmp_path / "log.csv"
    s = log_live(FakeConn(fail_at=5), ["RPM", "SPEED"], p, interval_s=0, max_samples=100, sleep=lambda s: None)
    assert s.stopped_by == "interrupt"
    rows = p.read_text(encoding="utf-8").splitlines()[1:]
    assert len(rows) == s.samples == 2 and all(r.count(",") == 3 for r in rows)
    ev = threading.Event()
    ev.set()
    s2 = log_live(FakeConn(), ["RPM"], tmp_path / "e.csv", interval_s=0, stop_event=ev, sleep=lambda s: None)
    assert s2.stopped_by == "stop_event" and s2.samples == 0


def test_T_O06_atomic_write_preserves_old_file(tmp_path, monkeypatch):
    """T-O06 — failure during replace leaves the previous JSON intact and no temp files; data integrity."""
    import os
    from tests.unit.test_ecus_models_report import sample_scan
    p = tmp_path / "scan.json"
    p.write_text("OLD", encoding="utf-8")

    def fail(*a, **k):
        raise OSError("disk full")
    monkeypatch.setattr(os, "replace", fail)
    with pytest.raises(OSError):
        write_json_atomic(p, sample_scan())
    assert p.read_text(encoding="utf-8") == "OLD"
    assert os.listdir(tmp_path) == ["scan.json"]


class FlakyTransport:
    def __init__(self, fatal_on=None):
        self.fatal_on = fatal_on

    def request(self, ecu, payload, *, allow_clear=False):
        if ecu.name == self.fatal_on:
            raise AdapterNotFoundError("serial port lost")
        if ecu.name == "B":
            raise BusError("CAN ERROR")
        from renault_diag.errors import NoResponseError
        raise NoResponseError("NO DATA")


def test_T_O07_scan_resilience():
    """T-O07 — per-ECU bus errors recorded, lost port aborts; D-013."""
    ecus = (EcuDef("A", "a", 0x700, 0x710), EcuDef("B", "b", 0x701, 0x711), EcuDef("C", "c", 0x702, 0x712))
    res = scan_all(FlakyTransport(), ecus)
    assert [r.ecu for r in res] == ["A", "B", "C"]
    assert res[1].error and "CAN ERROR" in res[1].error and not res[0].present
    with pytest.raises(AdapterNotFoundError):
        scan_all(FlakyTransport(fatal_on="B"), ecus)
