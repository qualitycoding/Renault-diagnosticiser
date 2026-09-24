"""ELM327 transport over pyserial (D-003, D-005, D-014)."""
import re
import time
from dataclasses import dataclass

import serial

from .ecus import EcuDef
from .elm_parse import parse_response
from .errors import (AdapterNotFoundError, AdapterUnsupportedError, NegativeResponseError,
                     NoResponseError, ProtocolError)
from .safety import check_at_command, check_request

_INIT_AT_SEQUENCE = ["Z", "E0", "L0", "S1", "H1", "SP6", "AL", "CAF1", "CFC1"]
_ADAPTER_TAGS = ("ELM327", "STN", "OBDLINK")
_VOLT_RE = re.compile(r"([0-9]+(?:\.[0-9]+)?)\s*V", re.IGNORECASE)
_MAX_PENDING_RETRIES = 10


@dataclass(frozen=True)
class AdapterInfo:
    version: str
    voltage_v: float | None


class Elm327Transport:
    def __init__(self, port: str, baudrate: int = 38400, timeout_s: float = 5.0,
                 serial_factory=None, trace_path=None):
        self.port = port
        self.baudrate = baudrate
        self.timeout_s = timeout_s
        self.serial_factory = serial_factory
        self.trace_path = trace_path
        self._ser = None
        self._current_ecu: EcuDef | None = None
        self._trace_fh = None

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, *exc):
        self.close()
        return False

    # ---------- lifecycle ----------

    def open(self) -> AdapterInfo:
        factory = self.serial_factory or serial.Serial
        try:
            self._ser = factory(self.port, self.baudrate, timeout=self.timeout_s)
        except (serial.SerialException, OSError) as e:
            raise AdapterNotFoundError(f"could not open {self.port!r}: {e}") from e

        if self.trace_path is not None:
            self._trace_fh = open(self.trace_path, "a", encoding="utf-8")

        self._current_ecu = None
        for cmd in _INIT_AT_SEQUENCE:
            self.at(cmd)

        version = self.at("I").strip()
        selftest = self.at("CRA7E8").strip()
        if selftest.upper() != "OK" or not any(tag in version.upper() for tag in _ADAPTER_TAGS):
            raise AdapterUnsupportedError(
                f"adapter self-test failed for {self.port!r}: ATI={version!r} ATCRA7E8={selftest!r}")
        self.at("CRA")

        voltage = self.read_voltage()
        return AdapterInfo(version=version, voltage_v=voltage)

    def close(self) -> None:
        if self._ser is not None:
            try:
                self._ser.close()
            finally:
                self._ser = None
        if self._trace_fh is not None:
            try:
                self._trace_fh.close()
            finally:
                self._trace_fh = None
        self._current_ecu = None

    # ---------- AT / raw I/O ----------

    def at(self, cmd: str) -> str:
        check_at_command(cmd)
        normalized = cmd.replace(" ", "").upper()
        wire_cmd = normalized if normalized.startswith("ST") else "AT" + normalized
        return self._send_raw(wire_cmd)

    def read_voltage(self) -> float | None:
        text = self.at("RV")
        m = _VOLT_RE.search(text)
        return float(m.group(1)) if m else None

    def _send_raw(self, wire_cmd: str) -> str:
        self._ser.write((wire_cmd + "\r").encode("ascii"))
        raw = self._read_until_prompt()
        text = raw.decode("ascii", errors="replace")
        if self.trace_fh_is_open():
            self._trace_fh.write(f">> {wire_cmd}\n<< {text!r}\n")
            self._trace_fh.flush()
        return self._strip_echo(text, wire_cmd)

    def trace_fh_is_open(self) -> bool:
        return self._trace_fh is not None

    def _read_until_prompt(self) -> bytes:
        buf = b""
        deadline = time.time() + self.timeout_s
        while not buf.endswith(b">"):
            if time.time() > deadline:
                raise NoResponseError(f"no prompt received from adapter within {self.timeout_s}s")
            chunk = self._ser.read(1)
            if not chunk:
                continue
            buf += chunk
        return buf[:-1]

    @staticmethod
    def _strip_echo(text: str, wire_cmd: str) -> str:
        lines = re.split(r"[\r\n]+", text)
        if lines and lines[0].replace(" ", "").upper() == wire_cmd:
            lines = lines[1:]
        return "\r".join(lines).strip()

    # ---------- ECU requests ----------

    def _select_ecu(self, ecu: EcuDef) -> None:
        if self._current_ecu is ecu or (self._current_ecu is not None and
                                        self._current_ecu.tx_id == ecu.tx_id and
                                        self._current_ecu.rx_id == ecu.rx_id):
            return
        self.at(f"SH{ecu.tx_id:03X}")
        self.at(f"CRA{ecu.rx_id:03X}")
        self.at(f"FCSH{ecu.tx_id:03X}")
        self.at("FCSD300000")
        self.at("FCSM1")
        self._current_ecu = ecu

    def request(self, ecu: EcuDef, payload: bytes, *, allow_clear: bool = False) -> bytes:
        check_request(payload, target=ecu, allow_clear=allow_clear)
        self._select_ecu(ecu)
        hexstr = payload.hex().upper()

        for _ in range(_MAX_PENDING_RETRIES):
            raw = self._send_raw(hexstr)
            if self.trace_fh_is_open():
                pass
            resp = parse_response(raw, ecu.rx_id)

            if resp and resp[0] == 0x7F:
                if len(resp) < 3:
                    raise ProtocolError(f"malformed negative response: {resp.hex()}")
                service, nrc = resp[1], resp[2]
                if nrc == 0x78:
                    continue
                raise NegativeResponseError(service, nrc)

            expected_sid = (payload[0] + 0x40) & 0xFF
            if not resp or resp[0] != expected_sid:
                got = resp.hex().upper() if resp else "<empty>"
                raise ProtocolError(
                    f"unexpected response SID for request {hexstr}: expected 0x{expected_sid:02X}, got {got}")
            return resp

        raise NoResponseError(
            f"no final response after {_MAX_PENDING_RETRIES} response-pending (0x78) replies")
