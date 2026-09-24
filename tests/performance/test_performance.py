# FROZEN — DO NOT MODIFY (see tests/FROZEN_MANIFEST.sha256, plan/DECISIONS.md)
import time

import pytest

from renault_diag.ecus import SCENIC3_ECUS, EcuDef
from renault_diag.logger import log_live
from renault_diag.manufacturer import scan_all
from renault_diag.transport import Elm327Transport

pytestmark = pytest.mark.performance


def test_T_P01_logger_throughput(obd_conn, tmp_path):
    """T-P01 — >= 50 samples/s for 4 PIDs against the emulator (software overhead only).
    Tolerance: emulator sustains ~3,100 queries/s (~775 4-PID samples/s, C-020); 50/s leaves >10x headroom
    for CI variance, so a miss indicates real overhead in our code. A-016."""
    t0 = time.perf_counter()
    s = log_live(obd_conn, ["RPM", "SPEED", "COOLANT_TEMP", "ENGINE_LOAD"], tmp_path / "p.csv",
                 interval_s=0, max_samples=200)
    rate = s.samples / (time.perf_counter() - t0)
    assert s.samples == 200 and rate >= 50, rate


def test_T_P02_full_scan_worst_case(emulator_port):
    """T-P02 — scan of 9 ECUs, 6 absent, completes <= 30 s with timeout_s=2 (A-016)."""
    absent = tuple(EcuDef(e.name, e.label, e.tx_id + 0x10 if e.name != "UCH" else e.tx_id, e.rx_id)
                   for e in SCENIC3_ECUS)
    with Elm327Transport(emulator_port, timeout_s=2) as t:
        t0 = time.perf_counter()
        res = scan_all(t, absent)
        dt = time.perf_counter() - t0
    assert len(res) == 9 and dt <= 30, dt
