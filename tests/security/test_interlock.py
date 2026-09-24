# FROZEN — DO NOT MODIFY (see tests/FROZEN_MANIFEST.sha256, plan/DECISIONS.md)
import pytest

from renault_diag.cli import main

pytestmark = pytest.mark.security


@pytest.mark.parametrize("speed_hex,expected_rc,session_sent", [("14", 5, False), ("00", 0, True)])
def test_T_S09_moving_vehicle_interlock(speed_hex, expected_rc, session_sent, tmp_path, fake_serial_factory,
                                        monkeypatch):
    """T-S09 — manufacturer scan refused (exit 5, no 10 C0 sent) when OBD speed > 0; proceeds at 0 km/h.
    Risk R-003; A-018; D-018. --manufacturer-only avoids python-OBD so the fake serial sees all traffic."""
    import renault_diag.transport as tr
    make, holder = fake_serial_factory
    monkeypatch.setattr(tr.serial, "Serial", make({"010D": "7E8 03 41 0D " + speed_hex}))
    rc = main(["scan", "--port", "FAKE", "--out", str(tmp_path / "s.json"), "--manufacturer-only"])
    assert rc == expected_rc
    assert ("10C0" in holder["serial"].sent_commands()) is session_sent
