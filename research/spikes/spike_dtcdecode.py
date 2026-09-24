"""Spike S5: python-OBD 0.7.3 2-byte DTC decoding (SAE J2012 letter mapping) (C-019)."""
from obd.decoders import parse_dtc
for b in [(0x01,0x33),(0x41,0x23),(0x81,0x00),(0xC1,0x55),(0x00,0x00)]:
    print(bytes(b).hex(), "->", parse_dtc(b))
