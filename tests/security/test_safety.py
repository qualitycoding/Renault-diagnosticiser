# FROZEN — DO NOT MODIFY (see tests/FROZEN_MANIFEST.sha256, plan/DECISIONS.md)
import pytest

from renault_diag.ecus import FUNCTIONAL_OBD, EcuDef
from renault_diag.errors import ForbiddenRequestError
from renault_diag.safety import check_at_command, check_request
from renault_diag.transport import Elm327Transport

pytestmark = pytest.mark.security
ECM = EcuDef("ECM", "Engine", 0x7E0, 0x7E8)
UCH = EcuDef("UCH", "Body", 0x745, 0x765)
AIRBAG = EcuDef("AIRBAG", "Airbag", 0x752, 0x772)

FORBIDDEN = ["11 01", "12 00", "23 00 00", "27 01", "28 00", "2E F1 90 00", "2F 01 00", "30 01", "31 01 00",
             "34 00", "35 00", "36 00", "37", "3B 01 00", "3D 00", "85 02", "10 02", "10 03", "10 85",
             "19 04 00 00 00 01", "14 FF FF FF", "04", "08 00", ""]
ALLOWED = ["01 00", "01 0C", "02 00 00", "03", "06 00", "07", "09 02", "0A", "10 C0", "10 01", "10 81",
           "3E 00", "3E", "17 FF 00", "18 00 FF 00", "19 02 AF", "19 01 FF", "19 0A", "1A 80", "21 01", "22 F1 90"]


@pytest.mark.parametrize("hexreq", FORBIDDEN)
def test_T_S01_forbidden_requests(hexreq):
    """T-S01 — everything outside the D-004 allowlist is refused; SC-7; C-018; A-005."""
    with pytest.raises(ForbiddenRequestError):
        check_request(bytes.fromhex(hexreq.replace(" ", "")), target=UCH)


@pytest.mark.parametrize("hexreq", ALLOWED)
def test_T_S02_allowed_requests(hexreq):
    """T-S02 — read-only allowlist passes; SC-7; D-004."""
    check_request(bytes.fromhex(hexreq.replace(" ", "")), target=UCH)


def test_T_S03_clear_only_engine_and_only_when_allowed():
    """T-S03 — mode 04 / service 14 only with allow_clear and ECM or functional target; A-005; D-004."""
    for tgt in (ECM, FUNCTIONAL_OBD):
        with pytest.raises(ForbiddenRequestError):
            check_request(b"\x04", target=tgt)
    check_request(b"\x04", target=FUNCTIONAL_OBD, allow_clear=True)
    check_request(b"\x04", target=ECM, allow_clear=True)
    check_request(bytes.fromhex("14FFFFFF"), target=ECM, allow_clear=True)
    for tgt in (UCH, AIRBAG):
        with pytest.raises(ForbiddenRequestError):
            check_request(bytes.fromhex("14FFFFFF"), target=tgt, allow_clear=True)
        with pytest.raises(ForbiddenRequestError):
            check_request(b"\x04", target=tgt, allow_clear=True)


@pytest.mark.parametrize("cmd,ok", [("Z", True), ("E0", True), ("SH745", True), ("SH 7E0", True), ("CRA765", True),
                                    ("CRA", True), ("FCSH745", True), ("FCSD300000", True), ("FCSM1", True),
                                    ("RV", True), ("SP6", True), ("ST FF", True), ("CAF1", True),
                                    ("PP 0C SV 23", False), ("PPFFON", False), ("@3 HELLO", False),
                                    ("MA", False), ("BRD 23", False), ("STFWU", False), ("STI", False),
                                    ("SP A", False), ("FCSD 30 08 00", False), ("CP 18", False),
                                    ("SH 18DAF1", False)])
def test_T_S04_at_allowlist(cmd, ok):
    """T-S04 — AT/ST allowlist incl. adapter-EEPROM writes blocked; A-011; D-004."""
    if ok:
        check_at_command(cmd)
    else:
        with pytest.raises(ForbiddenRequestError):
            check_at_command(cmd)


def test_T_S01b_nothing_written_when_forbidden(fake_serial_factory):
    """T-S01b — a forbidden request never reaches the serial port (not even header setup); SC-7; D-004."""
    make, holder = fake_serial_factory
    t = Elm327Transport("FAKE", serial_factory=make(), timeout_s=0.2)
    t.open()
    n = len(holder["serial"].writes)
    for hexreq in ["2EF19000", "3101FF00", "1101", "14FFFFFF"]:
        with pytest.raises(ForbiddenRequestError):
            t.request(UCH, bytes.fromhex(hexreq))
    with pytest.raises(ForbiddenRequestError):
        t.at("PP 0C SV 23")
    assert len(holder["serial"].writes) == n
