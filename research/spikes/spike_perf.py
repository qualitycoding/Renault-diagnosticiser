"""Spike S4: throughput of python-OBD queries against ELM327-emulator 4.0.0 (sets performance targets, C-020)."""
import threading, time, statistics, obd
from elm import Elm
obd.logger.setLevel(obd.logging.CRITICAL)
emu = Elm(batch_mode=True); emu.set_defaults(); emu.scenario='car'; emu.set_sorted_obd_msg()
port = emu.get_pty(); threading.Thread(target=emu.run, daemon=True).start(); time.sleep(0.5)
t0=time.perf_counter(); c=obd.OBD(port, fast=False, timeout=5); t_conn=time.perf_counter()-t0
cmds=[obd.commands.RPM, obd.commands.SPEED, obd.commands.COOLANT_TEMP, obd.commands.ENGINE_LOAD]
rates=[]
for rep in range(5):
    n=0; t=time.perf_counter()
    while time.perf_counter()-t<3:
        for cm in cmds:
            r=c.query(cm, force=True); assert not r.is_null(), cm; n+=1
    rates.append(n/(time.perf_counter()-t))
print(f"connect_s={t_conn:.2f} queries_per_s mean={statistics.mean(rates):.1f} min={min(rates):.1f} max={max(rates):.1f} stdev={statistics.stdev(rates):.2f}")
c.close(); emu.terminate()
