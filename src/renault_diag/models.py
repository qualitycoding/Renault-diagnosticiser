"""Scan result model + JSON (D-### interfaces). STUB (dataclass is final)."""
from dataclasses import dataclass, field

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
    raise NotImplementedError("S-009")


def from_json(s: str) -> ScanResult:
    raise NotImplementedError("S-009")


def write_json_atomic(path, r: ScanResult) -> None:
    raise NotImplementedError("S-009")
