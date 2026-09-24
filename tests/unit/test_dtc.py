# FROZEN — DO NOT MODIFY (see tests/FROZEN_MANIFEST.sha256, plan/DECISIONS.md)
import pytest

from renault_diag.dtc import Dtc, decode_kwp_17, decode_obd_pair, decode_uds_19_02, load_descriptions, status_flags
from renault_diag.errors import ProtocolError

pytestmark = pytest.mark.unit


@pytest.mark.parametrize("b0,b1,exp", [(0x01, 0x33, "P0133"), (0x41, 0x23, "C0123"), (0x81, 0x00, "B0100"),
                                       (0xC1, 0x55, "U0155"), (0x90, 0x07, "B1007"), (0x3F, 0xFF, "P3FFF"),
                                       (0x00, 0x00, None)])
def test_T_U01_decode_obd_pair(b0, b1, exp):
    """T-U01 — SAE letter mapping; requirement SC-2; claims C-019; decision D-009."""
    assert decode_obd_pair(b0, b1) == exp


def test_T_U02_uds_19_02_records_padding_and_zero():
    """T-U02 — UDS 19 02 decode incl. zero padding and all-zero records; SC-2; C-013; D-009."""
    payload = bytes.fromhex("5902FF" "9007412F" "000000FF" "C0018709" "0000")
    mask, dtcs = decode_uds_19_02(payload)
    assert mask == 0xFF
    assert dtcs == [Dtc("B1007-41", 0x2F, "uds", "9007412F"), Dtc("U0001-87", 0x09, "uds", "C0018709")]


def test_T_U02b_uds_19_02_empty_and_errors():
    """T-U02b — no DTCs; wrong SID/subfunction and truncated record raise ProtocolError; C-013."""
    assert decode_uds_19_02(bytes.fromhex("5902FF")) == (0xFF, [])
    for bad in ["5801FF", "5901FF", "59", "5902FF900741"]:
        with pytest.raises(ProtocolError):
            decode_uds_19_02(bytes.fromhex(bad))


def test_T_U06_status_flags_and_kwp():
    """T-U06 — ISO 14229 status bit names; KWP count + raw hex; C-013, C-022; D-009."""
    assert status_flags(0x00) == []
    assert status_flags(0x09) == ["testFailed", "confirmedDTC"]
    assert status_flags(0xFF) == ["testFailed", "testFailedThisOperationCycle", "pendingDTC", "confirmedDTC",
                                  "testNotCompletedSinceLastClear", "testFailedSinceLastClear",
                                  "testNotCompletedThisOperationCycle", "warningIndicatorRequested"]
    assert decode_kwp_17(bytes.fromhex("57020534680670")) == (2, "0534680670")
    assert decode_kwp_17(bytes.fromhex("5700")) == (0, "")
    with pytest.raises(ProtocolError):
        decode_kwp_17(bytes.fromhex("5902"))


def test_T_U07_load_descriptions(tmp_path):
    """T-U07 — user description CSV validation; SC-6; D-010."""
    good = tmp_path / "d.csv"
    good.write_text("code,description\nB1007-41,Door switch fault\nP0133,O2 sensor slow\n", encoding="utf-8")
    assert load_descriptions(good) == {"B1007-41": "Door switch fault", "P0133": "O2 sensor slow"}
    for body in ["code,description\nX1234,bad letter\n", "code,description\nP0133," + "a" * 201 + "\n",
                 "wrong,header\nP0133,x\n"]:
        bad = tmp_path / "b.csv"
        bad.write_text(body, encoding="utf-8")
        with pytest.raises(ValueError):
            load_descriptions(bad)
    big = tmp_path / "big.csv"
    big.write_text("code,description\n" + "P0133,x\n" * 10001, encoding="utf-8")
    with pytest.raises(ValueError):
        load_descriptions(big)
