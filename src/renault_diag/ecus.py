"""ECU address table (D-006, claims C-006/C-008). STUB (EcuDef and FUNCTIONAL_OBD are final)."""
from dataclasses import dataclass


@dataclass(frozen=True)
class EcuDef:
    name: str
    label: str
    tx_id: int
    rx_id: int


SCENIC3_ECUS: tuple[EcuDef, ...] = ()  # STUB: fill per plan/DECISIONS.md D-006 (S-002)

FUNCTIONAL_OBD = EcuDef("OBD", "Generic OBD (functional)", 0x7DF, 0x7E8)


def ecu_by_name(name: str) -> EcuDef:
    raise NotImplementedError("S-002")
