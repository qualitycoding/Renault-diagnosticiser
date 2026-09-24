"""Scan result model + JSON (D-### interfaces)."""
import dataclasses
import json
import os
import tempfile
from dataclasses import dataclass, field

from .dtc import Dtc
from .generic import GenericReport
from .manufacturer import EcuResult


@dataclass
class ScanResult:
    created_utc: str
    tool_version: str
    adapter: dict
    generic: GenericReport | None
    ecus: list[EcuResult] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    schema_version: int = 1


def to_json(r: ScanResult) -> str:
    return json.dumps(dataclasses.asdict(r), indent=2, sort_keys=True)


def _dtc_from_dict(d: dict) -> Dtc:
    return Dtc(code=d["code"], status=d["status"], source=d["source"], raw=d["raw"])


def _generic_from_dict(d: dict | None) -> GenericReport | None:
    if d is None:
        return None
    return GenericReport(
        vin=d["vin"], mil_on=d["mil_on"], dtc_count=d["dtc_count"],
        stored=[_dtc_from_dict(x) for x in d.get("stored", [])],
        pending=[_dtc_from_dict(x) for x in d.get("pending", [])],
        readiness=d.get("readiness", {}), protocol=d.get("protocol", ""),
        supported=d.get("supported", []),
    )


def _ecu_from_dict(d: dict) -> EcuResult:
    return EcuResult(
        ecu=d["ecu"], present=d["present"], protocol=d.get("protocol"),
        session_ok=d.get("session_ok", False),
        dtcs=[_dtc_from_dict(x) for x in d.get("dtcs", [])],
        kwp_dtc_count=d.get("kwp_dtc_count"), kwp_raw=d.get("kwp_raw"), error=d.get("error"),
    )


def from_json(s: str) -> ScanResult:
    d = json.loads(s)
    if d.get("schema_version") != 1:
        raise ValueError(f"unsupported schema_version: {d.get('schema_version')!r}")
    return ScanResult(
        created_utc=d["created_utc"], tool_version=d["tool_version"], adapter=d["adapter"],
        generic=_generic_from_dict(d.get("generic")),
        ecus=[_ecu_from_dict(x) for x in d.get("ecus", [])],
        warnings=d.get("warnings", []), schema_version=d["schema_version"],
    )


def write_json_atomic(path, r: ScanResult) -> None:
    path = str(path)
    directory = os.path.dirname(path) or "."
    text = to_json(r)
    fd, tmp_path = tempfile.mkstemp(dir=directory, prefix=".renault_diag_", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)
    except BaseException:
        try:
            os.remove(tmp_path)
        except OSError:
            pass
        raise
