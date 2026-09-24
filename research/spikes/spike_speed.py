"""Spike S9: stationary SPEED override answers both python-OBD and a raw functional 010D request (T-S09 fixture validity)."""
import sys, threading, time
sys.path.insert(0, ".")
import obd, serial
from elm import Elm
from tests.conftest import _build_scenario, SCENARIO
obd.logger.setLevel(obd.logging.CRITICAL)
_build_scenario()
emu = Elm(batch_mode=True); emu.set_defaults(); emu.scenario = SCENARIO; emu.set_sorted_obd_msg()
port = emu.get_pty(); threading.Thread(target=emu.run, daemon=True).start(); time.sleep(0.5)
s = serial.Serial(port, 38400, timeout=2)
def q(c):
    s.write((c + "\r").encode()); b = b""; t = time.time()
    while not b.endswith(b">") and time.time() - t < 5: b += s.read(1)
    return b.decode(errors="replace").replace("\r", " | ").strip()
for c in ["ATZ", "ATE0", "ATS1", "ATH1", "ATSP6", "ATSH7DF", "ATCRA7E8", "010D", "ATCRA"]: print(c, "->", q(c))
s.close()
c = obd.OBD(port, fast=False, timeout=5)
print("python-OBD SPEED:", c.query(obd.commands.SPEED).value, "| RPM:", c.query(obd.commands.RPM).value,
      "| SPEED supported:", obd.commands.SPEED in c.supported_commands)
c.close(); emu.terminate()
