# FROZEN — DO NOT MODIFY (see tests/FROZEN_MANIFEST.sha256, plan/DECISIONS.md)
import pytest

from renault_diag.ecus import EcuDef
from renault_diag.errors import (AdapterNotFoundError, AdapterUnsupportedError, NegativeResponseError,
                                 ProtocolError)
from renault_diag.transport import Elm327Transport

pytestmark = pytest.mark.unit
UCH = EcuDef("UCH", "Body", 0x745, 0x765)
ABS = EcuDef("ABS", "ABS", 0x740, 0x760)


def open_t(make, script=None):
    factory = make(script)
    t = Elm327Transport("FAKE", serial_factory=factory, timeout_s=0.2)
    info = t.open()
    return t, info


def test_T_U10_open_sequence_and_selftest(fake_serial_factory):
    """T-U10 — init sequence and D-014 self-test; SC-1; C-011, C-016; D-005, D-014."""
    make, holder = fake_serial_factory
    t, info = open_t(make)
    cmds = holder["serial"].sent_commands()
    for c in ["ATZ", "ATE0", "ATH1", "ATSP6", "ATCAF1", "ATCRA7E8"]:
        assert c in cmds
    assert "ELM327" in info.version and info.voltage_v == pytest.approx(12.6)
    t.close()
    make2, holder2 = fake_serial_factory
    with pytest.raises(AdapterUnsupportedError):
        open_t(make2, {"ATCRA7E8": "?"})


def test_T_U10b_headers_set_once_and_request(fake_serial_factory):
    """T-U10b — headers only re-sent on ECU change; positive response returned; D-005."""
    make, holder = fake_serial_factory
    t, _ = open_t(make, {"10C0": "765 02 50 C0", "3E00": "765 02 7E 00"})
    before = len(holder["serial"].writes)
    assert t.request(UCH, bytes.fromhex("10C0")) == bytes.fromhex("50C0")
    assert t.request(UCH, bytes.fromhex("3E00")) == bytes.fromhex("7E00")
    cmds = holder["serial"].sent_commands()[before:]
    assert cmds.count("ATSH745") == 1 and "ATCRA765" in cmds and "ATFCSH745" in cmds
    assert "ATFCSD300000" in cmds and "ATFCSM1" in cmds


def test_T_U10c_nrc_pending_and_errors(fake_serial_factory):
    """T-U10c — NRC → NegativeResponseError; 78 pending re-read; wrong SID → ProtocolError; D-005."""
    make, holder = fake_serial_factory
    t, _ = open_t(make, {"10C0": "765 03 7F 10 12",
                         "1902AF": ["765 03 7F 19 78", "765 03 59 02 FF"],
                         "22F190": "765 03 59 02 FF"})
    with pytest.raises(NegativeResponseError) as ei:
        t.request(UCH, bytes.fromhex("10C0"))
    assert (ei.value.service, ei.value.nrc) == (0x10, 0x12)
    assert t.request(UCH, bytes.fromhex("1902AF")) == bytes.fromhex("5902FF")
    with pytest.raises(ProtocolError):
        t.request(UCH, bytes.fromhex("22F190"))


def test_T_U10d_port_not_found():
    """T-U10d — unopenable port → AdapterNotFoundError; SC-1; operational."""
    def boom(*a, **k):
        import serial
        raise serial.SerialException("could not open port")
    with pytest.raises(AdapterNotFoundError):
        Elm327Transport("/dev/does-not-exist", serial_factory=boom).open()
