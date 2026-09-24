"""Generic OBD-II/EOBD via python-OBD (D-002). STUB (dataclass is final)."""
from dataclasses import dataclass, field

from .dtc import Dtc


@dataclass
class GenericReport:
    vin: str | None
    mil_on: bool | None
    dtc_count: int | None
    stored: list[Dtc] = field(default_factory=list)
    pending: list[Dtc] = field(default_factory=list)
    readiness: dict[str, str] = field(default_factory=dict)
    protocol: str = ""
    supported: list[str] = field(default_factory=list)


def read_generic(conn) -> GenericReport:
    raise NotImplementedError("S-007")
