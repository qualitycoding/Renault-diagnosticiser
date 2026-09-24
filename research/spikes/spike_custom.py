"""Spike S3: in-process emulator with custom Renault-style scenario (UCH 745/765 UDS 1902) (C-013)."""
import threading, time, serial
from elm import Elm
from elm.obd_message import ObdMessage, HD, SZ, DT, ELM_FOOTER
ObdMessage['renault_test'] = dict(ObdMessage['car'])
ObdMessage['renault_test']['UCH_SESSION'] = {'Request': '^10C0' + ELM_FOOTER, 'Descr': 'UCH session', 'Header': '745',
    'Response': HD('765') + SZ('02') + DT('50 C0')}
ObdMessage['renault_test']['UCH_DTC'] = {'Request': '^1902FF' + ELM_FOOTER, 'Descr': 'UCH DTC', 'Header': '745',
    'Response': HD('765') + SZ('07') + DT('59 02 FF 90 07 41 2F')}
emu = Elm(batch_mode=True)
emu.set_defaults(); emu.scenario='renault_test'; emu.set_sorted_obd_msg()
port = emu.get_pty()
th = threading.Thread(target=emu.run, daemon=True); th.start(); time.sleep(0.5)
s=serial.Serial(port,38400,timeout=2)
def q(c):
    s.write((c+"\r").encode()); buf=b""; t=time.time()
    while not buf.endswith(b">") and time.time()-t<5: buf+=s.read(1)
    r=buf.decode(errors="replace").replace("\r"," | ").strip(); print(f"{c!r:14} -> {r}")
for c in ["ATZ","ATE0","ATH1","ATSP6","ATSH745","ATCRA765","10C0","1902FF","ATSH7E0","ATCRA7E8","1902FF","ATSH7DF","ATCRA","03"]: q(c)
s.close(); emu.terminate()
