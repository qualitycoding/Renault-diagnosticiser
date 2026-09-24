"""ELM327 response parsing + ISO-TP reassembly (D-005)."""
import re

from .errors import BufferFullError, BusError, NoResponseError, ProtocolError

_ERR_NO_DATA = "NO DATA"
_ERR_BUS = ("CAN ERROR", "BUS ERROR", "BUS INIT", "UNABLE TO CONNECT")
_ERR_BUFFER = "BUFFER FULL"
_ERR_PROTO = "?"

_HEX = "0-9A-Fa-f"


def _split_lines(text: str) -> list[str]:
    raw = re.split(r"[\r\n]+", text)
    return [ln.strip() for ln in raw if ln.strip()]


def _is_noise(line: str) -> bool:
    u = line.upper()
    return u in ("OK", "SEARCHING...") or u.startswith("SEARCHING")


def parse_response(text: str, rx_id: int) -> bytes:
    lines = _split_lines(text)

    for line in lines:
        if _ERR_BUFFER in line.upper():
            raise BufferFullError(f"adapter reported BUFFER FULL: {line!r}")

    for line in lines:
        u = line.upper()
        if u == _ERR_NO_DATA:
            raise NoResponseError("adapter reported NO DATA")
        if any(u.startswith(b) or b in u for b in _ERR_BUS):
            raise BusError(f"adapter reported a bus error: {line!r}")
        if u == _ERR_PROTO:
            raise ProtocolError(f"adapter reported '?': unrecognised command")

    frame_lines = [ln for ln in lines if not _is_noise(ln)]

    id_hex = f"{rx_id:03X}"
    id_pat_spaced = re.compile(rf"^{id_hex}\s+([{_HEX}]{{2}}(?:\s*[{_HEX}]{{2}})*)$")
    id_pat_compact = re.compile(rf"^{id_hex}([{_HEX}]+)$")

    frames: list[list[int]] = []
    for line in frame_lines:
        compact_spaces = re.sub(r"\s+", " ", line).strip()
        m = id_pat_spaced.match(compact_spaces)
        if m:
            hexstr = m.group(1).replace(" ", "")
        else:
            no_space = line.replace(" ", "")
            m2 = id_pat_compact.match(no_space)
            if not m2:
                continue
            hexstr = m2.group(1)
        if len(hexstr) % 2 != 0:
            raise ProtocolError(f"odd-length hex frame from {id_hex}: {line!r}")
        byte_list = [int(hexstr[i:i + 2], 16) for i in range(0, len(hexstr), 2)]
        frames.append(byte_list)

    if not frames:
        raise ProtocolError(f"no frames found from rx_id 0x{rx_id:03X} in response")

    messages = _reassemble_iso_tp(frames)

    if not messages:
        raise ProtocolError("frames present but no complete ISO-TP message could be reassembled")

    final_candidates = [m for m in messages if not (len(m) >= 3 and m[0] == 0x7F and m[2] == 0x78)]
    if final_candidates:
        return bytes(final_candidates[-1])
    return bytes(messages[-1])


def _reassemble_iso_tp(frames: list[list[int]]) -> list[bytes]:
    messages: list[bytes] = []
    i = 0
    n = len(frames)
    while i < n:
        frame = frames[i]
        if not frame:
            i += 1
            continue
        pci = frame[0]
        pci_type = (pci >> 4) & 0xF

        if pci_type == 0x0:
            length = pci & 0xF
            data = frame[1:]
            if len(data) < length:
                raise ProtocolError(f"single-frame declared length {length} exceeds available data")
            messages.append(bytes(data[:length]))
            i += 1
            continue

        if pci_type == 0x1:
            length = ((pci & 0x0F) << 8) | frame[1]
            payload = list(frame[2:])
            expected_seq = 1
            j = i + 1
            while len(payload) < length:
                if j >= n:
                    raise ProtocolError("incomplete multi-frame ISO-TP message: ran out of frames")
                cf = frames[j]
                cf_pci = cf[0]
                cf_type = (cf_pci >> 4) & 0xF
                cf_seq = cf_pci & 0xF
                if cf_type != 0x2:
                    raise ProtocolError(f"expected consecutive frame (21..2F), got PCI 0x{cf_pci:02X}")
                if cf_seq != expected_seq:
                    raise ProtocolError(
                        f"consecutive frame out of sequence: expected {expected_seq}, got {cf_seq}")
                payload.extend(cf[1:])
                expected_seq = (expected_seq + 1) & 0xF
                j += 1
            if len(payload) < length:
                raise ProtocolError("incomplete multi-frame ISO-TP message: length mismatch")
            messages.append(bytes(payload[:length]))
            i = j
            continue

        i += 1

    return messages
