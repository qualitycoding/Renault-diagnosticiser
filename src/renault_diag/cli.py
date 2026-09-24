"""Command-line interface (D-### interfaces)."""
import argparse
import json
import sys
import time

import obd
import serial.tools.list_ports

from . import __version__
from .dtc import load_descriptions
from .ecus import FUNCTIONAL_OBD, SCENIC3_ECUS, ecu_by_name
from .errors import (AdapterNotFoundError, AdapterUnsupportedError, BufferFullError, BusError,
                     DiagError, ForbiddenRequestError, NegativeResponseError, NoResponseError,
                     ProtocolError)
from .generic import read_generic
from .logger import log_live
from .manufacturer import EcuResult, scan_all, scan_ecu
from .models import ScanResult, from_json, write_json_atomic
from .report import render_html
from .transport import Elm327Transport

_DEFAULT_LOG_PIDS = ["RPM", "SPEED", "COOLANT_TEMP", "ENGINE_LOAD", "INTAKE_PRESSURE", "MAF"]
_CLEAR_PHRASE = "CLEAR ENGINE CODES"


def _now_utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _interlock_speed_ok(t) -> tuple[bool | None, str | None]:
    """Returns (moving, warning). moving is True/False/None (unknown = interlock could not run)."""
    try:
        resp = t.request(FUNCTIONAL_OBD, bytes.fromhex("010D"))
    except NoResponseError:
        return None, "could not read vehicle speed for the moving-vehicle interlock"
    except (BusError, BufferFullError, ProtocolError, NegativeResponseError) as e:
        return None, f"interlock speed probe failed: {e}"
    if len(resp) < 3:
        return None, "interlock speed probe returned a malformed response"
    speed_kmh = resp[2]
    return (speed_kmh > 0), None


def _build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="renault-diag")
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("ports")

    ca = sub.add_parser("check-adapter")
    ca.add_argument("--port", required=True)

    sc = sub.add_parser("scan")
    sc.add_argument("--port", required=True)
    sc.add_argument("--out", required=True)
    group = sc.add_mutually_exclusive_group()
    group.add_argument("--generic-only", action="store_true")
    group.add_argument("--manufacturer-only", action="store_true")
    sc.add_argument("--ecu", action="append", default=[])
    sc.add_argument("--trace")

    lg = sub.add_parser("log")
    lg.add_argument("--port", required=True)
    lg.add_argument("--out", required=True)
    lg.add_argument("--pids", nargs="+")
    lg.add_argument("--interval", type=float, default=0.5)
    lg.add_argument("--duration", type=float, default=None)

    rp = sub.add_parser("report")
    rp.add_argument("--scan", required=True)
    rp.add_argument("--out", required=True)
    rp.add_argument("--log")
    rp.add_argument("--show-vin", action="store_true")
    rp.add_argument("--descriptions")

    cl = sub.add_parser("clear-engine-codes")
    cl.add_argument("--port", required=True)
    cl.add_argument("--backup-dir", required=True)

    return p


def _cmd_ports(args) -> int:
    for info in serial.tools.list_ports.comports():
        print(f"{info.device}\t{info.description}")
    return 0


def _open_transport(port: str, trace_path=None):
    """Returns (transport, adapter_info) or raises AdapterNotFoundError/AdapterUnsupportedError."""
    t = Elm327Transport(port, trace_path=trace_path)
    info = t.open()
    return t, info


def _cmd_check_adapter(args) -> int:
    try:
        t, info = _open_transport(args.port)
    except (AdapterNotFoundError, AdapterUnsupportedError) as e:
        print(str(e), file=sys.stderr)
        return 3
    print(f"version: {info.version}")
    print(f"voltage: {info.voltage_v}")
    t.close()
    return 0


def _cmd_scan(args) -> int:
    warnings: list[str] = []
    adapter_dict = {"version": None, "voltage_v": None}
    ecus: list[EcuResult] = []
    generic = None
    speed_state: bool | None = None

    do_manufacturer = not args.generic_only
    do_generic = not args.manufacturer_only

    target_ecus = SCENIC3_ECUS
    if args.ecu:
        try:
            target_ecus = tuple(ecu_by_name(n) for n in args.ecu)
        except ValueError as e:
            print(str(e), file=sys.stderr)
            return 2

    if do_manufacturer:
        try:
            t, info = _open_transport(args.port, trace_path=args.trace)
        except (AdapterNotFoundError, AdapterUnsupportedError) as e:
            print(str(e), file=sys.stderr)
            return 3
        adapter_dict = {"version": info.version, "voltage_v": info.voltage_v}
        if info.voltage_v is not None and info.voltage_v < 12.0:
            warnings.append(f"adapter voltage low: {info.voltage_v}V")

        speed_state, warn = _interlock_speed_ok(t)
        if warn:
            warnings.append(warn)
        if speed_state is True:
            t.close()
            print("vehicle must be stationary", file=sys.stderr)
            return 5

        ecus = scan_all(t, target_ecus)
        t.close()

    if do_generic:
        conn = None
        try:
            conn = obd.OBD(args.port, fast=False, timeout=5)
            if conn.is_connected():
                generic = read_generic(conn)
            else:
                warnings.append("generic OBD connection failed")
        except Exception as e:  # noqa: BLE001 - surfaced as a warning, not fatal
            warnings.append(f"generic OBD error: {e}")
        finally:
            if conn is not None:
                conn.close()

    any_ecu_present = any(e.present for e in ecus)
    if generic is None and not any_ecu_present and speed_state is None:
        print("no response from the vehicle", file=sys.stderr)
        return 4

    result = ScanResult(created_utc=_now_utc(), tool_version=__version__, adapter=adapter_dict,
                        generic=generic, ecus=ecus, warnings=warnings)
    try:
        write_json_atomic(args.out, result)
    except OSError as e:
        print(str(e), file=sys.stderr)
        return 2
    return 0


def _cmd_log(args) -> int:
    conn = obd.OBD(args.port, fast=False, timeout=5)
    if not conn.is_connected():
        print(f"could not connect to adapter/vehicle on {args.port}", file=sys.stderr)
        conn.close()
        return 3

    if args.pids:
        pids = args.pids
    else:
        supported_names = {c.name for c in conn.supported_commands}
        pids = [p for p in _DEFAULT_LOG_PIDS if p in supported_names]
        dropped = [p for p in _DEFAULT_LOG_PIDS if p not in supported_names]
        if dropped:
            print(f"warning: unsupported PIDs dropped: {', '.join(dropped)}", file=sys.stderr)
        if not pids:
            print("no supported PIDs to log", file=sys.stderr)
            conn.close()
            return 2

    try:
        summary = log_live(conn, pids, args.out, interval_s=args.interval, max_duration_s=args.duration)
    except ValueError as e:
        print(str(e), file=sys.stderr)
        conn.close()
        return 2
    conn.close()
    print(f"wrote {summary.samples} samples to {summary.path} (stopped: {summary.stopped_by})")
    return 0


def _cmd_report(args) -> int:
    try:
        with open(args.scan, "r", encoding="utf-8") as f:
            text = f.read()
    except OSError as e:
        print(str(e), file=sys.stderr)
        return 2
    try:
        scan = from_json(text)
    except (ValueError, KeyError) as e:
        print(str(e), file=sys.stderr)
        return 2

    descriptions = None
    if args.descriptions:
        try:
            descriptions = load_descriptions(args.descriptions)
        except ValueError as e:
            print(str(e), file=sys.stderr)
            return 2

    html = render_html(scan, log_path=args.log, show_vin=args.show_vin, descriptions=descriptions)
    try:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(html)
    except OSError as e:
        print(str(e), file=sys.stderr)
        return 2
    return 0


def _build_clear_backup(t) -> ScanResult:
    warnings: list[str] = []
    try:
        raw = t.request(FUNCTIONAL_OBD, bytes.fromhex("03"))
        warnings.append(f"pre-clear mode 03 raw response: {raw.hex().upper()}")
    except DiagError as e:
        warnings.append(f"pre-clear mode 03 read failed: {e}")

    ecm = ecu_by_name("ECM")
    ecm_result = scan_ecu(t, ecm)
    return ScanResult(created_utc=_now_utc(), tool_version=__version__, adapter={}, generic=None,
                      ecus=[ecm_result], warnings=warnings)


def _cmd_clear(args, input_fn) -> int:
    try:
        t, info = _open_transport(args.port)
    except (AdapterNotFoundError, AdapterUnsupportedError) as e:
        print(str(e), file=sys.stderr)
        return 3

    speed_state, warn = _interlock_speed_ok(t)
    if speed_state is True:
        t.close()
        print("vehicle must be stationary", file=sys.stderr)
        return 5

    backup = _build_clear_backup(t)
    backup.adapter = {"version": info.version, "voltage_v": info.voltage_v}
    backup_path = f"{args.backup_dir.rstrip('/')}/pre-clear-{_now_utc().replace(':', '')}.json"
    try:
        write_json_atomic(backup_path, backup)
    except OSError as e:
        t.close()
        print(str(e), file=sys.stderr)
        return 2

    print("This will erase stored engine fault codes, freeze-frame data, and reset readiness "
         "monitors. An MOT/emissions test may fail until the monitors complete again.")
    print(f"A backup of the current state was saved to {backup_path}.")
    answer = input_fn(f"Type {_CLEAR_PHRASE} to continue: ")
    if answer != _CLEAR_PHRASE:
        t.close()
        print("not confirmed; nothing cleared", file=sys.stderr)
        return 5

    try:
        t.request(FUNCTIONAL_OBD, b"\x04", allow_clear=True)
    except DiagError as e:
        t.close()
        print(str(e), file=sys.stderr)
        return 2
    t.close()
    print("engine fault codes cleared")
    return 0


def main(argv: list[str] | None = None, *, input_fn=input) -> int:
    parser = _build_argparser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as e:
        return e.code if isinstance(e.code, int) else 2

    try:
        if args.command == "ports":
            return _cmd_ports(args)
        if args.command == "check-adapter":
            return _cmd_check_adapter(args)
        if args.command == "scan":
            return _cmd_scan(args)
        if args.command == "log":
            return _cmd_log(args)
        if args.command == "report":
            return _cmd_report(args)
        if args.command == "clear-engine-codes":
            return _cmd_clear(args, input_fn)
        return 2
    except ForbiddenRequestError as e:
        print(str(e), file=sys.stderr)
        return 5
    except (AdapterNotFoundError, AdapterUnsupportedError) as e:
        print(str(e), file=sys.stderr)
        return 3
    except KeyboardInterrupt:
        return 130
