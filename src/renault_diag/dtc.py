"""DTC decoding (D-009, D-010)."""
import csv
import re
from dataclasses import dataclass

from .errors import ProtocolError

_LETTER = {0b00: "P", 0b01: "C", 0b10: "B", 0b11: "U"}

_STATUS_BIT_NAMES = [
    "testFailed",
    "testFailedThisOperationCycle",
    "pendingDTC",
    "confirmedDTC",
    "testNotCompletedSinceLastClear",
    "testFailedSinceLastClear",
    "testNotCompletedThisOperationCycle",
    "warningIndicatorRequested",
]

_CODE_RE = re.compile(r"^[PCBU][0-9A-F]{4}(-[0-9A-F]{2})?$")


@dataclass(frozen=True)
class Dtc:
    code: str
    status: int | None
    source: str  # "obd" | "uds" | "kwp"
    raw: str


def _pair_code_text(b0: int, b1: int) -> str:
    letter = _LETTER[(b0 >> 6) & 0b11]
    digit = (b0 >> 4) & 0b11
    low_nibble = b0 & 0x0F
    return f"{letter}{digit}{low_nibble:01X}{b1:02X}"


def decode_obd_pair(b0: int, b1: int) -> str | None:
    if b0 == 0 and b1 == 0:
        return None
    return _pair_code_text(b0, b1)


def decode_uds_19_02(payload: bytes) -> tuple[int, list[Dtc]]:
    if len(payload) < 2 or payload[0] != 0x59 or payload[1] != 0x02:
        raise ProtocolError(f"not a ReadDTCInformation reportDTCByStatusMask response: {payload.hex()}")
    if len(payload) < 3:
        raise ProtocolError(f"UDS 19 02 response too short: {payload.hex()}")
    mask = payload[2]
    body = payload[3:]

    dtcs: list[Dtc] = []
    i = 0
    while i < len(body):
        remaining = len(body) - i
        if remaining < 4:
            if body[i:] == bytes(remaining):
                break
            raise ProtocolError(f"truncated UDS DTC record: {body[i:].hex()}")
        record = body[i:i + 4]
        b0, b1, ftype, status = record
        if b0 == 0 and b1 == 0 and ftype == 0:
            i += 4
            continue
        code_text = _pair_code_text(b0, b1)
        code = f"{code_text}-{ftype:02X}"
        dtcs.append(Dtc(code, status, "uds", record.hex().upper()))
        i += 4

    return mask, dtcs


def decode_kwp_17(payload: bytes) -> tuple[int, str]:
    if len(payload) < 2 or payload[0] != 0x57:
        raise ProtocolError(f"not a KWP 17 FF DTC response: {payload.hex()}")
    count = payload[1]
    raw = payload[2:].hex().upper()
    return count, raw


def status_flags(status: int) -> list[str]:
    return [name for bit, name in enumerate(_STATUS_BIT_NAMES) if status & (1 << bit)]


def load_descriptions(path) -> dict[str, str]:
    result: dict[str, str] = {}
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration:
            raise ValueError(f"{path}: empty file, expected header 'code,description'")
        if header != ["code", "description"]:
            raise ValueError(f"{path}: header must be exactly ['code', 'description'], got {header!r}")

        for line_no, row in enumerate(reader, start=2):
            if line_no > 10_001:
                raise ValueError(f"{path}: too many rows (max 10000 data rows)")
            if len(row) != 2:
                raise ValueError(f"{path}:{line_no}: expected 2 columns, got {row!r}")
            code, desc = row
            if not _CODE_RE.match(code):
                raise ValueError(f"{path}:{line_no}: invalid code {code!r}")
            if len(desc) > 200:
                raise ValueError(f"{path}:{line_no}: description exceeds 200 characters")
            result[code] = desc

    return result
