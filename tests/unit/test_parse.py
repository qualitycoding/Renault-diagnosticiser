# FROZEN — DO NOT MODIFY (see tests/FROZEN_MANIFEST.sha256, plan/DECISIONS.md)
import pytest

from renault_diag.elm_parse import parse_response
from renault_diag.errors import BufferFullError, BusError, NoResponseError, ProtocolError

pytestmark = pytest.mark.unit


def test_T_U04_single_frame_spaces_on_and_off():
    """T-U04 — SF with/without spaces, echo & SEARCHING ignored, other IDs ignored; SC-2; C-011; D-005."""
    assert parse_response("765 02 50 C0 ", 0x765) == bytes.fromhex("50C0")
    assert parse_response("SEARCHING...\r7E8064100BE3FA813", 0x7E8) == bytes.fromhex("4100BE3FA813")
    assert parse_response("7E9 03 41 0D 00\r7E8 03 41 0D 32", 0x7E8) == bytes.fromhex("410D32")


def test_T_U04b_multi_frame_reassembly():
    """T-U04b — FF + CF reassembly with padding removal; C-026 fixture format."""
    text = "765 10 0F 59 02 FF 90 07 41\r765 21 2F 90 08 42 2F C0 01\r765 22 87 09 00 00 00 00 00"
    assert parse_response(text, 0x765) == bytes.fromhex("5902FF9007412F9008422FC0018709")


def test_T_U04c_response_pending_then_final():
    """T-U04c — 7F xx 78 discarded, last message returned; D-005 interface rule."""
    assert parse_response("765 03 7F 19 78\r765 03 59 02 FF", 0x765) == bytes.fromhex("5902FF")
    assert parse_response("765 03 7F 19 78", 0x765) == bytes.fromhex("7F1978")


@pytest.mark.parametrize("text,exc", [("NO DATA", NoResponseError), ("CAN ERROR", BusError),
                                      ("BUS INIT: ...ERROR", BusError), ("UNABLE TO CONNECT", BusError),
                                      ("765 10 0F 59 02 FF 90 07 41 BUFFER FULL", BufferFullError),
                                      ("?", ProtocolError),
                                      ("765 10 0F 59 02 FF 90 07 41\r765 22 2F 90 08 42 2F C0 01", ProtocolError),
                                      ("765 10 0F 59 02 FF 90 07 41", ProtocolError),
                                      ("7E8 02 50 C0", ProtocolError)])
def test_T_U03_error_responses(text, exc):
    """T-U03 — terminal/error responses and malformed ISO-TP; C-024; D-005."""
    with pytest.raises(exc):
        parse_response(text, 0x765)
