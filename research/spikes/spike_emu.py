"""Spike S1: python-OBD 0.7.3 <-> ELM327-emulator 4.0.0 over pty (claims C-001,C-002,C-010)."""
import subprocess, time, sys, obd, os, tempfile
out = tempfile.mktemp()
p = subprocess.Popen([sys.executable,"-m","elm","-s","car","-b",out], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
port=None
for _ in range(100):
    time.sleep(0.2)
    if os.path.exists(out) and open(out).readline().strip():
        port=open(out).readline().strip(); break
print("port",port)
c=obd.OBD(port, fast=False, timeout=5)
print("status",c.status(),"| proto",c.protocol_name(), c.protocol_id())
for name in ["RPM","COOLANT_TEMP","SPEED","GET_DTC","STATUS","ELM_VOLTAGE","ELM_VERSION","FUEL_STATUS"]:
    r=c.query(getattr(obd.commands,name), force=True); print(name,"=>", r.value)
print("supported count", len(c.supported_commands))
# raw custom command: Renault-style header switch
from obd import OBDCommand
from obd.protocols import ECU
c.close(); p.terminate()
