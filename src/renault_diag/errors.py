"""Exception hierarchy (D-### interfaces). Implemented at plan time."""


class DiagError(Exception):
    """Base class for all renault_diag errors."""


class AdapterNotFoundError(DiagError):
    """Serial port could not be opened or was lost."""


class AdapterUnsupportedError(DiagError):
    """Adapter failed the D-014 self-test."""


class NoResponseError(DiagError):
    """Adapter reported NO DATA / timeout."""


class BusError(DiagError):
    """CAN ERROR, BUS ERROR, BUS INIT...ERROR, UNABLE TO CONNECT."""


class BufferFullError(DiagError):
    """Adapter reported BUFFER FULL."""


class ProtocolError(DiagError):
    """Malformed or unexpected response."""


class ForbiddenRequestError(DiagError):
    """Request blocked by the D-004 safety allowlist before transmission."""


class NegativeResponseError(DiagError):
    """ECU answered 7F <service> <nrc>."""

    def __init__(self, service: int, nrc: int):
        super().__init__(f"negative response: service 0x{service:02X}, NRC 0x{nrc:02X}")
        self.service = service
        self.nrc = nrc
