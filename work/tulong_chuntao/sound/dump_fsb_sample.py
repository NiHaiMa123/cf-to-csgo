# -*- coding: utf-8 -*-
from __future__ import annotations
import json, struct, sys
from pathlib import Path
sys.path.insert(0, str(Path(r"D:\project\cf_to_csgo\scripts")))
import _paths
BANK = Path(_paths.cf_dir()) / "rez" / "FMODStudio" / "Weapon" / "Weapon.bank"

def fsb5_names(data: bytes):
    off = data.find(b"FSB5")
    print("FSB5 at", off)
    version, n_samples, sh_size, name_size, data_size, mode = struct.unpack_from("<IIIIII", data, off + 4)
    print(dict(version=version, n=n_samples, sh=sh_size, namesz=name_size, mode=mode))
    name_off = off + 60 + sh_size
    table = data[name_off:name_off + name_size]
    names = []
    start = 0
    for _ in range(n_samples):
        end = table.find(b"\x00", start)
        if end < 0:
            break
        names.append(table[start:end].decode("utf-8", errors="replace"))
        start = end + 1
    return names

names = fsb5_names(BANK.read_bytes())
print("parsed", len(names))
print("first20", names[:20])
needles = ("KUK", "KNIFE", "BEAST", "ATTACK", "SELECT", "HIT")
for n in names:
    u = n.upper()
    if any(t in u for t in needles) and ("KUK" in u or "KNIFE" in u or "BEAST" in u):
        print(" ", n)
print("--- all names with Kuk/Knife/Select ---")
for i, n in enumerate(names, 1):
    u = n.upper()
    if "KUK" in u or n.upper().startswith("KNIFE") or "KUKRI" in u:
        print(i, n)
