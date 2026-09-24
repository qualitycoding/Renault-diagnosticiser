"""Request/AT-command allowlist (D-004)."""
import re

from .ecus import EcuDef
from .errors import ForbiddenRequestError

# Services fully allowed regardless of subfunction/data.
_ALLOWED_SIMPLE_SIDS = {0x01, 0x02, 0x03, 0x06, 0x07, 0x09, 0x0A,
                        0x17, 0x18, 0x1A, 0x21, 0x22}
_SID_10_ALLOWED_SUB = {0xC0, 0x01, 0x81}
_SID_19_ALLOWED_SUB = {0x01, 0x02, 0x0A}
_CLEAR_SIDS = {0x04, 0x14}

_AT_EXACT = {
    "Z", "WS", "D", "E0", "E1", "L0", "L1", "S0", "S1", "H0", "H1", "AL",
    "CAF0", "CAF1", "CFC1", "SP6", "SP0", "DP", "DPN", "RV", "I", "@1",
    "AT0", "AT1", "AT2",
}
_AT_PATTERNS = [
    re.compile(r"^SH[0-9A-F]{3}$"),
    re.compile(r"^CRA([0-9A-F]{3})?$"),
    re.compile(r"^FCSH[0-9A-F]{3}$"),
    re.compile(r"^FCSD300000$"),
    re.compile(r"^FCSM1$"),
    re.compile(r"^ST[0-9A-F]{2}$"),
]


def check_request(payload: bytes, *, target: EcuDef, allow_clear: bool = False) -> None:
    if not payload:
        raise ForbiddenRequestError("empty request payload")
    sid = payload[0]

    if sid in _CLEAR_SIDS:
        if not allow_clear:
            raise ForbiddenRequestError(f"service 0x{sid:02X} requires allow_clear=True")
        if target.tx_id not in (0x7E0, 0x7DF):
            raise ForbiddenRequestError(
                f"service 0x{sid:02X} only allowed against ECM (7E0) or functional OBD (7DF), "
                f"got target tx_id=0x{target.tx_id:03X}")
        return

    if sid == 0x10:
        if len(payload) < 2 or payload[1] not in _SID_10_ALLOWED_SUB:
            raise ForbiddenRequestError(f"service 0x10 subfunction not allowed: {payload.hex()}")
        return

    if sid == 0x19:
        if len(payload) < 2 or payload[1] not in _SID_19_ALLOWED_SUB:
            raise ForbiddenRequestError(f"service 0x19 subfunction not allowed: {payload.hex()}")
        return

    if sid == 0x3E:
        if len(payload) > 2:
            raise ForbiddenRequestError(f"service 0x3E payload too long: {payload.hex()}")
        return

    if sid in _ALLOWED_SIMPLE_SIDS:
        return

    raise ForbiddenRequestError(f"service 0x{sid:02X} is not in the allowlist: {payload.hex()}")


def check_at_command(cmd: str) -> None:
    normalized = cmd.replace(" ", "").upper()
    if normalized.startswith("AT"):
        normalized = normalized[2:]

    if normalized in _AT_EXACT:
        return
    for pat in _AT_PATTERNS:
        if pat.match(normalized):
            return
    raise ForbiddenRequestError(f"AT/ST command not allowed: {cmd!r}")
