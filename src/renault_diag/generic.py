"""Generic OBD-II/EOBD via python-OBD (D-002, D-017)."""
import re
from dataclasses import dataclass, field

import obd

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


def _readiness_state(test) -> str:
    if not getattr(test, "available", False):
        return "unavailable"
    return "complete" if getattr(test, "complete", False) else "incomplete"


def _extract_vin(conn) -> str | None:
    """D-017: python-OBD 0.7.3 truncates VIN.value; decode from the raw ISO-TP message bytes instead."""
    resp = conn.query(obd.commands.VIN, force=True)
    if resp.is_null() or not resp.messages:
        return None
    data = bytes(resp.messages[0].data)
    candidate = data[3:20]
    text = "".join(chr(b) for b in candidate if 32 <= b < 127)
    text = re.sub(r"[^A-Za-z0-9]", "", text)
    return text or None


def _dtc_list(pairs, source: str) -> list[Dtc]:
    out = []
    for code, _desc in pairs or []:
        if code:
            out.append(Dtc(code, None, source, code))
    return out


def read_generic(conn) -> GenericReport:
    vin = _extract_vin(conn)

    status_resp = conn.query(obd.commands.STATUS)
    mil_on = None
    dtc_count = None
    readiness: dict[str, str] = {}
    if not status_resp.is_null():
        st = status_resp.value
        mil_on = bool(st.MIL)
        dtc_count = int(st.DTC_count)
        for name, test in vars(st).items():
            if hasattr(test, "available") and hasattr(test, "complete") and name:
                readiness[name] = _readiness_state(test)

    stored_resp = conn.query(obd.commands.GET_DTC)
    pending_resp = conn.query(obd.commands.GET_CURRENT_DTC)
    stored = _dtc_list(None if stored_resp.is_null() else stored_resp.value, "obd")
    pending = _dtc_list(None if pending_resp.is_null() else pending_resp.value, "obd")

    protocol = conn.protocol_name() or ""
    supported = sorted(c.name for c in conn.supported_commands)

    return GenericReport(vin=vin, mil_on=mil_on, dtc_count=dtc_count, stored=stored, pending=pending,
                         readiness=readiness, protocol=protocol, supported=supported)
