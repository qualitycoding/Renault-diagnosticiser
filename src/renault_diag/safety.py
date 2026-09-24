"""Request/AT-command allowlist (D-004). STUB."""
from .ecus import EcuDef


def check_request(payload: bytes, *, target: EcuDef, allow_clear: bool = False) -> None:
    raise NotImplementedError("S-003")


def check_at_command(cmd: str) -> None:
    raise NotImplementedError("S-003")
