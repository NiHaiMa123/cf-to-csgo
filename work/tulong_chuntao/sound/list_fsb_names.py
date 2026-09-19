# -*- coding: utf-8 -*-
"""Parse FSB5 name table in Weapon.bank for Kukri streams."""
from __future__ import annotations

import struct
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO / "scripts"))
import _paths  # noqa: E402

BANK = Path(_paths.cf_dir()) / "rez" / "FMODStudio" / "Weapon" / "Weapon.bank"
OUT = Path(__file__).resolve().parent / "kukri_streams.json"


def fsb5_names(data: bytes) -> list[str]:
    # FMOD bank may wrap FSB5. Find magic.
    off = data.find(b"FSB5")
    if off < 0:
        raise RuntimeError("no FSB5 magic")
    version, n_samples, sh_size, name_size, data_size, mode = struct.unpack_from(
        "<IIIIII", data, off + 4)
    name_off = off + 60 + sh_size
    table = data[name_off:name_off + name_size]
    names = []
    start = 0
    for i in range(n_samples):
        end = table.find(b"\x00", start)
        if end < 0:
            break
        names.append(table[start:end].decode("utf-8", errors="replace"))
        start = end + 1
    return names


def main() -> int:
    data = BANK.read_bytes()
    names = fsb5_names(data)
    print(f"streams={len(names)}")
    hits = []
    for i, n in enumerate(names, start=1):
        if "KUKRI" in n.upper():
            hits.append({"subsong": i, "name": n})
            print(f"  {i:4d}  {n}")
    import json
    OUT.write_text(json.dumps({"bank": str(BANK), "total": len(names), "kukri": hits}, indent=1), encoding="utf-8")
    print("kukri", len(hits))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
