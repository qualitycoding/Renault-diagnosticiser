"""DTC decoding (D-009, D-010). STUB (dataclass is final)."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Dtc:
    code: str
    status: int | None
    source: str  # "obd" | "uds" | "kwp"
    raw: str


def decode_obd_pair(b0: int, b1: int) -> str | None:
    raise NotImplementedError("S-005")


def decode_uds_19_02(payload: bytes) -> tuple[int, list[Dtc]]:
    raise NotImplementedError("S-005")


def decode_kwp_17(payload: bytes) -> tuple[int, str]:
    raise NotImplementedError("S-005")


def status_flags(status: int) -> list[str]:
    raise NotImplementedError("S-005")


def load_descriptions(path) -> dict[str, str]:
    raise NotImplementedError("S-005")
