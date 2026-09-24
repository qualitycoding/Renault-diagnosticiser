"""Live PID logging to CSV (D-### interfaces). STUB (dataclass is final)."""
import time
from dataclasses import dataclass


@dataclass(frozen=True)
class LogSummary:
    samples: int
    path: str
    resumed: bool
    stopped_by: str


def log_live(conn, pids, out_path, *, interval_s=0.5, max_samples=None,
             max_duration_s=None, stop_event=None, sleep=time.sleep) -> LogSummary:
    raise NotImplementedError("S-010")
