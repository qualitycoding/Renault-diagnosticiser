"""Spike S6: multi-frame (ISO-TP FF/CF) response on a Renault-style header in ELM327-emulator 4.0.0."""
import threading, time, serial
from elm import Elm
from elm.obd_message import ObdMessage, HD, SZ, DT, ELM_FOOTER, PA, ST
sc = dict(ObdMessage['car'])
sc['UCH_DTC'] = {'Request': '^1902AF' + ELM_FOOTER, 'Descr': 'x', 'Header': '745',
    'Response': ST('765 10 0F 59 02 FF 90 07 41') + ST('765 21 2F 90 08 42 2F C0 01') + ST('765 22 87 09 00 00 00 00 00')}
sc['UCH_ID'] = {'Request': '^22F190' + ELM_FOOTER, 'Descr': 'y', 'Header': '745', 'Response': PA('62 F1 90 56 46 31 4A 5A 30 30 30 30 30 30 30 30 30 30 30 31')}
ObdMessage['mf']=sc
emu=Elm(batch_mode=True); emu.set_defaults(); emu.scenario='mf'; emu.set_sorted_obd_msg()
port=emu.get_pty(); threading.Thread(target=emu.run,daemon=True).start(); time.sleep(0.5)
s=serial.Serial(port,38400,timeout=2)
def q(c):
    s.write((c+"\r").encode()); buf=b""; t=time.time()
    while not buf.endswith(b">") and time.time()-t<5: buf+=s.read(1)
    print(f"{c!r:12} -> {buf.decode(errors='replace')!r}")
for c in ["ATZ","ATE0","ATH1","ATS1","ATSP6","ATSH745","ATCRA765","ATFCSH745","ATFCSD300000","ATFCSM1","1902AF","ATS0","1902AF","ATH0","1902AF"]: q(c)
emu.terminate()
