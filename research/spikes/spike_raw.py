"""Spike S2: raw ELM327 dialogue with header switching against ELM327-emulator (C-011, C-012)."""
import subprocess, time, sys, os, tempfile, serial
out=tempfile.mktemp()
p=subprocess.Popen([sys.executable,"-m","elm","-s","car","-b",out],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(100):
    time.sleep(0.2)
    if os.path.exists(out) and open(out).readline().strip(): break
port=open(out).readline().strip()
s=serial.Serial(port,38400,timeout=2)
def q(c):
    s.write((c+"\r").encode()); buf=b""
    t=time.time()
    while not buf.endswith(b">") and time.time()-t<5: buf+=s.read(1)
    r=buf.decode(errors="replace").replace("\r"," | ").strip(); print(f"{c!r:16} -> {r}"); return r
for c in ["ATZ","ATE0","ATL0","ATS0","ATH1","ATSP6","0100","03","0902","ATSH7E0","ATCRA7E8","ATFCSH7E0","ATFCSD300000","ATFCSM1","10C0","22F190","1902FF","ATSH745","ATCRA765","10C0","1902FF","ATCRA","ATD"]:
    q(c)
s.close(); p.terminate()
