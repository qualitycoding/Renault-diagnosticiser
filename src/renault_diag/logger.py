"""Live PID logging to CSV (D-### interfaces)."""
import csv
import os
import time
from dataclasses import dataclass


@dataclass(frozen=True)
class LogSummary:
    samples: int
    path: str
    resumed: bool
    stopped_by: str


def _value_to_cell(value):
    if value is None:
        return ""
    magnitude = getattr(value, "magnitude", None)
    if magnitude is not None:
        return magnitude
    return value


def log_live(conn, pids, out_path, *, interval_s=0.5, max_samples=None,
             max_duration_s=None, stop_event=None, sleep=time.sleep) -> LogSummary:
    out_path = str(out_path)
    supported = {c.name: c for c in conn.supported_commands}
    for name in pids:
        if name not in supported:
            raise ValueError(f"unsupported PID: {name!r}")

    header = "timestamp_utc,elapsed_s," + ",".join(pids)
    file_exists = os.path.exists(out_path)
    resumed = False

    if file_exists:
        with open(out_path, "r", encoding="utf-8", newline="") as f:
            first_line = f.readline().rstrip("\r\n")
        if first_line != header:
            raise ValueError(
                f"{out_path}: existing header {first_line!r} does not match requested {header!r}")
        resumed = True

    mode = "a" if resumed else "w"
    samples = 0
    stopped_by = "unknown"
    start = time.perf_counter()

    with open(out_path, mode, encoding="utf-8", newline="") as f:
        if not resumed:
            f.write(header + "\n")
            f.flush()

        try:
            while True:
                if stop_event is not None and stop_event.is_set():
                    stopped_by = "stop_event"
                    break
                if max_samples is not None and samples >= max_samples:
                    stopped_by = "max_samples"
                    break
                elapsed = time.perf_counter() - start
                if max_duration_s is not None and elapsed >= max_duration_s:
                    stopped_by = "max_duration"
                    break

                values = []
                for name in pids:
                    resp = conn.query(supported[name], force=True)
                    values.append(_value_to_cell(None if resp.is_null() else resp.value))

                ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                row = [ts, f"{elapsed:.3f}"] + [str(v) for v in values]
                f.write(",".join(row) + "\n")
                f.flush()
                samples += 1

                if samples % 10 == 0:
                    os.fsync(f.fileno())

                sleep(interval_s)
        except KeyboardInterrupt:
            stopped_by = "interrupt"

    return LogSummary(samples=samples, path=out_path, resumed=resumed, stopped_by=stopped_by)
