# -*- coding: utf-8 -*-
import sys, json
from pathlib import Path
sys.path.insert(0, r"D:\project\cf_to_csgo\scripts\material_recovery")
import n05a_decoder_provenance_audit as audit
CF = audit.CF
KEYS = ("RENEWAL", "ARM_", "_ARM", "HAND")
seen = set()
rezdir = CF / "rez"
out = {}
for idx in sorted(list(rezdir.glob("*.rez")) + list(rezdir.glob("*.REZ"))):
    try:
        entries = audit.read_rez_index_mmap(idx)
    except Exception:
        continue
    for e in entries:
        p = e["full_path"].upper()
        if not p.endswith((".DTX", ".TGA")): continue
        if any(k in p for k in KEYS) and p not in seen:
            seen.add(p); out.setdefault(idx.name, []).append(e["full_path"])
json.dump(out, open(r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\source\armtex_index.json","w"), indent=1)
for k,v in out.items():
    print("##",k,len(v))
    for x in v[:60]: print("  ",x)
