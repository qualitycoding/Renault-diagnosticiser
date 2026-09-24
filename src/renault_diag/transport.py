"""ELM327 transport over pyserial (D-003, D-005, D-014). STUB."""
from dataclasses import dataclass

import serial

from .ecus import EcuDef


@dataclass(frozen=True)
class AdapterInfo:
    version: str
    voltage_v: float | None


class Elm327Transport:
    def __init__(self, port: str, baudrate: int = 38400, timeout_s: float = 5.0,
                 serial_factory=None):
        # None → serial.Serial looked up at open() time (allows monkeypatching, T-S08)
        self.port = port
        self.baudrate = baudrate
        self.timeout_s = timeout_s
        self.serial_factory = serial_factory

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, *exc):
        self.close()
        return False

    def open(self) -> AdapterInfo:
        raise NotImplementedError("S-006")

    def close(self) -> None:
        raise NotImplementedError("S-006")

    def at(self, cmd: str) -> str:
        raise NotImplementedError("S-006")

    def read_voltage(self) -> float | None:
        raise NotImplementedError("S-006")

    def request(self, ecu: EcuDef, payload: bytes, *, allow_clear: bool = False) -> bytes:
        raise NotImplementedError("S-006")
