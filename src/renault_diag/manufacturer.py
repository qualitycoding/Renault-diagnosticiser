"""Renault ECU scan (D-007, D-008, D-013)."""
from dataclasses import dataclass, field

from .dtc import decode_kwp_17, decode_uds_19_02
from .ecus import SCENIC3_ECUS, EcuDef
from .errors import (AdapterNotFoundError, BufferFullError, BusError, NegativeResponseError,
                     NoResponseError, ProtocolError)


@dataclass
class EcuResult:
    ecu: str
    present: bool
    protocol: str | None = None
    session_ok: bool = False
    dtcs: list = field(default_factory=list)
    kwp_dtc_count: int | None = None
    kwp_raw: str | None = None
    error: str | None = None


def scan_ecu(t, ecu: EcuDef) -> EcuResult:
    session_ok = False
    try:
        t.request(ecu, bytes.fromhex("10C0"))
        session_ok = True
    except NoResponseError:
        return EcuResult(ecu.name, present=False, error="no response")
    except NegativeResponseError:
        session_ok = False
    except (BusError, BufferFullError, ProtocolError) as e:
        return EcuResult(ecu.name, present=False, error=str(e))

    try:
        resp = t.request(ecu, bytes.fromhex("1902AF"))
        mask, dtcs = decode_uds_19_02(resp)
        return EcuResult(ecu.name, present=True, protocol="uds", session_ok=session_ok, dtcs=dtcs)
    except NegativeResponseError as e:
        if e.nrc in (0x11, 0x12):
            try:
                resp = t.request(ecu, bytes.fromhex("17FF00"))
                count, raw = decode_kwp_17(resp)
                return EcuResult(ecu.name, present=True, protocol="kwp", session_ok=session_ok,
                                 kwp_dtc_count=count, kwp_raw=raw)
            except NoResponseError:
                return EcuResult(ecu.name, present=False, error="no response")
            except (BusError, BufferFullError, ProtocolError, NegativeResponseError) as e2:
                return EcuResult(ecu.name, present=False, error=str(e2))
        return EcuResult(ecu.name, present=False, error=str(e))
    except NoResponseError:
        return EcuResult(ecu.name, present=False, error="no response")
    except (BusError, BufferFullError, ProtocolError) as e:
        return EcuResult(ecu.name, present=False, error=str(e))


def scan_all(t, ecus=SCENIC3_ECUS) -> list[EcuResult]:
    results = []
    for ecu in ecus:
        try:
            results.append(scan_ecu(t, ecu))
        except AdapterNotFoundError:
            raise
    return results
