"""Spike S8: python-OBD 0.7.3 VIN decoding against emulator — decoded value vs raw message data."""
import sys, threading, time
sys.path.insert(0, ".")
import obd
from elm import Elm
from tests.conftest import _build_scenario, SCENARIO
obd.logger.setLevel(obd.logging.CRITICAL)
_build_scenario()
emu = Elm(batch_mode=True); emu.set_defaults(); emu.scenario = SCENARIO; emu.set_sorted_obd_msg()
port = emu.get_pty(); threading.Thread(target=emu.run, daemon=True).start(); time.sleep(0.5)
c = obd.OBD(port, fast=False, timeout=5)
r = c.query(obd.commands.VIN, force=True)
print("decoded:", repr(r.value))
for m in r.messages:
    print("msg data:", bytes(m.data).hex(), "| frames:", [bytes(f.raw.encode()) if isinstance(f.raw,str) else f.raw for f in m.frames])
d = bytes(r.messages[0].data)
print("candidate VIN from raw data[3:]:", d[3:].decode(errors="replace"), len(d[3:]))
c.close(); emu.terminate()
