"""Spike S7 (cold-read validation of frozen tests): python-OBD Status API, VIN, supported PIDs used by
T-I01/T-P01, socket-free operation (T-I03), header reset between raw transport and python-OBD, absent-ECU timing (T-P02)."""
import socket, sys, threading, time
sys.path.insert(0, ".")
from tests.conftest import _build_scenario, SCENARIO
import obd, serial
from elm import Elm
obd.logger.setLevel(obd.logging.CRITICAL)
_build_scenario()
emu = Elm(batch_mode=True); emu.set_defaults(); emu.scenario = SCENARIO; emu.set_sorted_obd_msg()
port = emu.get_pty(); threading.Thread(target=emu.run, daemon=True).start(); time.sleep(0.5)
real_socket = socket.socket
def no_net(*a, **k): raise AssertionError("network")
socket.socket = no_net
s = serial.Serial(port, 38400, timeout=2)
def q(c):
    s.write((c + "\r").encode()); b = b""; t = time.time()
    while not b.endswith(b">") and time.time() - t < 5: b += s.read(1)
    return b.decode(errors="replace").strip()
t0 = time.time()
for c in ["ATZ","ATE0","ATL0","ATS1","ATH1","ATSP6","ATAL","ATCAF1","ATCFC1","ATI","ATCRA7E8","ATCRA","ATRV"]: print(c, "->", q(c).replace("\r"," | "))
for tx in ["7F0","750","752","753","754","745","762","765","7F1"]:
    q("ATSH"+tx); r = q("10C0"); print(tx, "10C0 ->", r.replace("\r"," | "))
print("9 session probes took %.2fs" % (time.time()-t0))
s.close()
c = obd.OBD(port, fast=False, timeout=5)
print("connected", c.is_connected(), c.protocol_name())
st = c.query(obd.commands.STATUS).value
print("MIL", st.MIL, "DTC_count", st.DTC_count, "ignition", st.ignition_type)
print("readiness:", {k: (v.available, v.complete) for k, v in vars(st).items() if hasattr(v, "available")})
vin = c.query(obd.commands.VIN, force=True).value; print("VIN", repr(vin))
names = {x.name for x in c.supported_commands}
print("supported has:", {n: n in names for n in ["RPM","SPEED","COOLANT_TEMP","ENGINE_LOAD","GET_DTC","GET_CURRENT_DTC","VIN"]})
print("GET_DTC", c.query(obd.commands.GET_DTC).value, "GET_CURRENT_DTC", c.query(obd.commands.GET_CURRENT_DTC).value)
c.close(); emu.terminate(); socket.socket = real_socket
