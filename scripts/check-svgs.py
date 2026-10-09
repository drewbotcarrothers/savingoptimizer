#!/usr/bin/env python3
"""Fail if any SVG under assets/ is not well-formed UTF-8 XML.

Browsers show nothing for an <img src="*.svg"> that does not parse (stray Latin-1 bytes such as a lone 0xB7 or
0xA2, C0 control bytes left where a curly quote or dash lost its high byte, or a bare '<' or '&' in text).
Usage: python3 scripts/check-svgs.py
"""
import sys
import xml.dom.minidom as minidom
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
bad = []
for p in sorted((ROOT / "assets").rglob("*.svg")):
    try:
        minidom.parseString(p.read_bytes().decode("utf-8").encode("utf-8"))
    except Exception as e:  # UnicodeDecodeError or ExpatError
        bad.append(f"{p.relative_to(ROOT)}: {e}")
print(f"svgs checked; {len(bad)} not well-formed")
for b in bad: print("  " + b)
sys.exit(1 if bad else 0)
