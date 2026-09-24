# FROZEN — DO NOT MODIFY (see tests/FROZEN_MANIFEST.sha256, plan/DECISIONS.md)
"""Shared fixtures: scripted fake serial (unit/security) and in-process ELM327 emulator (integration).
Requirements: D-012, C-010, C-026."""
import threading
import time

import pytest


class FakeSerial:
    """Scripted stand-in for serial.Serial. Every write is recorded in .writes.
    script maps a normalised command (upper-case, no spaces, no CR) to the response text
    (without the trailing prompt). Unknown AT commands answer 'OK'; unknown others answer 'NO DATA'."""

    DEFAULTS = {"ATZ": "ELM327 v1.5", "ATI": "ELM327 v1.5", "ATRV": "12.6V", "AT@1": "OBDII to RS232 Interpreter"}

    def __init__(self, script=None, *args, **kwargs):
        self.script = dict(self.DEFAULTS)
        self.script.update(script or {})
        self.writes = []
        self._buf = b""
        self.is_open = True
        self.timeout = kwargs.get("timeout", 1)

    def write(self, data):
        self.writes.append(data)
        cmd = data.decode().replace(" ", "").replace("\r", "").replace("\n", "").upper()
        resp = self.script.get(cmd)
        if resp is None:
            resp = "OK" if cmd.startswith("AT") else "NO DATA"
        if isinstance(resp, list):
            resp = resp.pop(0) if len(resp) > 1 else resp[0]
        self._buf += (resp + "\r\r>").encode()
        return len(data)

    def read(self, n=1):
        out, self._buf = self._buf[:n], self._buf[n:]
        return out

    def read_until(self, expected=b"\n", size=None):
        i = self._buf.find(expected)
        if i < 0:
            out, self._buf = self._buf, b""
        else:
            out, self._buf = self._buf[: i + len(expected)], self._buf[i + len(expected):]
        return out

    @property
    def in_waiting(self):
        return len(self._buf)

    def reset_input_buffer(self):
        self._buf = b""

    def flush(self):
        pass

    def close(self):
        self.is_open = False

    def sent_commands(self):
        return [w.decode().strip().replace(" ", "").upper() for w in self.writes]


@pytest.fixture
def fake_serial_factory():
    """Returns (factory, holder); holder['serial'] is the FakeSerial created by the transport."""
    holder = {}

    def make(script=None):
        def factory(*args, **kwargs):
            s = FakeSerial(script, *args, **kwargs)
            holder["serial"] = s
            return s
        return factory

    return make, holder


# ---------- emulator ----------
SCENARIO = "renault_scenic3_test"

# Expected decoded content of the scenario (used by integration tests).
EXPECTED_UCH_DTCS = [("B1007-41", 0x2F), ("B1008-42", 0x2F), ("U0001-87", 0x09)]
EXPECTED_ECM_KWP = (2, "0534680670")


def _build_scenario():
    from elm.obd_message import ObdMessage, ELM_FOOTER, ST
    sc = dict(ObdMessage["car"])

    def add(key, header, request, *lines):
        resp = ST(lines[0])
        for ln in lines[1:]:
            resp += ST(ln)
        sc[key] = {"Request": "^" + request + ELM_FOOTER, "Descr": key, "Header": header, "Response": resp}

    add("T_ECM_SESSION", "7E0", "10C0", "7E8 02 50 C0")
    add("T_ECM_UDS", "7E0", "1902AF", "7E8 03 7F 19 11")
    add("T_ECM_KWP", "7E0", "17FF00", "7E8 07 57 02 05 34 68 06 70")
    add("T_UCH_SESSION", "745", "10C0", "765 02 50 C0")
    add("T_UCH_DTC", "745", "1902AF", "765 10 0F 59 02 FF 90 07 41", "765 21 2F 90 08 42 2F C0 01",
        "765 22 87 09 00 00 00 00 00")
    add("T_AIRBAG_SESSION", "752", "10C0", "772 03 7F 10 12")
    add("T_AIRBAG_DTC", "752", "1902AF", "772 03 59 02 FF")
    # Vehicle stationary (R-003 interlock, T-S09): override the stock scenario's 10 km/h speed.
    from elm.obd_message import HD, SZ, DT
    sc["SPEED"] = {"Request": "^010D" + ELM_FOOTER, "Descr": "Vehicle Speed (stationary)", "Header": "7E0",
                   "Response": HD("7E8") + SZ("03") + DT("41 0D 00")}
    ObdMessage[SCENARIO] = sc


@pytest.fixture
def emulator_port():
    """Start ELM327-emulator 4.0.0 in-process with the Renault test scenario; yield its pty path."""
    elm_mod = pytest.importorskip("elm")
    _build_scenario()
    emu = elm_mod.Elm(batch_mode=True)
    emu.set_defaults()
    emu.scenario = SCENARIO
    emu.set_sorted_obd_msg()
    port = emu.get_pty()
    t = threading.Thread(target=emu.run, daemon=True)
    t.start()
    time.sleep(0.5)
    yield port
    emu.terminate()


@pytest.fixture
def obd_conn(emulator_port):
    import obd
    obd.logger.setLevel(obd.logging.CRITICAL)
    c = obd.OBD(emulator_port, fast=False, timeout=5)
    assert c.is_connected()
    yield c
    c.close()
