"""Renault ECU scan (D-007, D-008, D-013). STUB (dataclass is final)."""
from dataclasses import dataclass, field

from .dtc import Dtc
from .ecus import SCENIC3_ECUS


@dataclass
class EcuResult:
    ecu: str
    present: bool
    protocol: str | None = None
    session_ok: bool = False
    dtcs: list[Dtc] = field(default_factory=list)
    kwp_dtc_count: int | None = None
    kwp_raw: str | None = None
    error: str | None = None


def scan_ecu(t, ecu) -> EcuResult:
    raise NotImplementedError("S-008")


def scan_all(t, ecus=SCENIC3_ECUS) -> list[EcuResult]:
    raise NotImplementedError("S-008")
