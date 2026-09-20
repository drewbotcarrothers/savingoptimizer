#!/usr/bin/env python3
"""Strip/replace illegal XML control chars in SVG article charts."""
from pathlib import Path
import sys

MAP = {
    0x1C: '"',  # open quote stand-in
    0x1D: '"',  # close quote stand-in
    0x18: "'",
    0x19: "'",
    0x13: "\u2013",  # en dash
    0x14: "\u2014",  # em dash
    0x12: "\u2212",  # minus
}

def fix_bytes(data: bytes) -> bytes:
    out = bytearray()
    for b in data:
        if b in MAP:
            out.extend(MAP[b].encode("utf-8"))
        elif b < 0x20 and b not in (0x9, 0x0A, 0x0D):
            continue
        else:
            out.append(b)
    return bytes(out)

def has_illegal(data: bytes) -> bool:
    return any(b < 0x20 and b not in (0x9, 0x0A, 0x0D) for b in data)

def main(root: Path) -> int:
    svgs = sorted(root.glob("*.svg"))
    changed = []
    for p in svgs:
        raw = p.read_bytes()
        if not has_illegal(raw):
            continue
        fixed = fix_bytes(raw)
        if fixed != raw:
            p.write_bytes(fixed)
            changed.append(p.name)
    print(f"scanned={len(svgs)} fixed={len(changed)}")
    for name in changed:
        print(name)
    # verify
    left = [p.name for p in svgs if has_illegal(p.read_bytes())]
    if left:
        print("REMAINING_BAD", len(left))
        for n in left:
            print(n)
        return 1
    return 0

if __name__ == "__main__":
    root = Path(sys.argv[1] if len(sys.argv) > 1 else "assets/articles")
    raise SystemExit(main(root))
