# -*- coding: utf-8 -*-
"""List unique PLAYERVIEW DragonBlade / peach-ish filenames from index_hits.json."""
from __future__ import annotations

import json
from pathlib import Path

hits = json.loads((Path(__file__).parent / "index_hits.json").read_text(encoding="utf-8"))
print("=== PLAYERVIEW LTB unique ===")
seen = set()
for h in hits["hits"]:
    fp = h["full_path"].replace("\\", "/")
    if "/PLAYERVIEW/" in fp.upper() and fp.upper().endswith(".LTB"):
        if fp not in seen:
            seen.add(fp)
            print(f"{h['size']:8d}  {h['archive']:18s}  {fp}")
print("=== PLAYERVIEW DTX unique ===")
seen = set()
for h in hits["hits"]:
    fp = h["full_path"].replace("\\", "/")
    if "/PLAYERVIEW/" in fp.upper() and fp.upper().endswith(".DTX"):
        if fp not in seen:
            seen.add(fp)
            print(f"{h['size']:8d}  {h['archive']:18s}  {fp}")
print("=== WeaponShader CFG unique ===")
seen = set()
for h in hits["hits"]:
    fp = h["full_path"].replace("\\", "/")
    if "WeaponShader" in fp and fp.upper().endswith(".CFG"):
        if fp not in seen:
            seen.add(fp)
            print(f"{h['size']:8d}  {h['archive']:18s}  {fp}")
