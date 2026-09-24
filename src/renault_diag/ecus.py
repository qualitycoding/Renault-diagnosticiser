"""ECU address table (D-006, claims C-006/C-008)."""
from dataclasses import dataclass


@dataclass(frozen=True)
class EcuDef:
    name: str
    label: str
    tx_id: int
    rx_id: int


SCENIC3_ECUS: tuple[EcuDef, ...] = (
    EcuDef("ECM", "Engine control (injection)", 0x7E0, 0x7E8),
    EcuDef("ABS", "ABS / ESP", 0x740, 0x760),
    EcuDef("EPS", "Electric power steering", 0x742, 0x762),
    EcuDef("TDB", "Instrument cluster", 0x743, 0x763),
    EcuDef("HVAC", "Climate control", 0x744, 0x764),
    EcuDef("UCH", "Body control module", 0x745, 0x765),
    EcuDef("AIRBAG", "Airbag / pretensioners", 0x752, 0x772),
    EcuDef("APB", "Automatic parking brake", 0x755, 0x775),
    EcuDef("AT", "Automatic gearbox", 0x7E1, 0x7E9),
)

FUNCTIONAL_OBD = EcuDef("OBD", "Generic OBD (functional)", 0x7DF, 0x7E8)


def ecu_by_name(name: str) -> EcuDef:
    for e in SCENIC3_ECUS + (FUNCTIONAL_OBD,):
        if e.name.lower() == name.lower():
            return e
    raise ValueError(f"unknown ECU name: {name!r}")
