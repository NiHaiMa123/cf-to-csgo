# -*- coding: utf-8 -*-
import sys
from pathlib import Path
sys.path.insert(0, r"D:\project\cf_to_csgo\scripts\material_recovery")
import n05a_decoder_provenance_audit as audit
from rez_verified_payload import read_verified_payload

OUT = Path(r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\source\armtex")
for rezdir, name in [(CF:=audit.CF, "rez2/RF017.REZ"), (CF, "rez/rf017.rez"), (CF, "rez2/RF016.REZ"), (CF,"rez/RF016.REZ")]:
    idx = rezdir/"rez2"/"RF017.REZ" if "rez2" in name else rezdir/"rez"/name.split("/")[-1]
    if not idx.exists(): continue
    try: entries = audit.read_rez_index_mmap(idx)
    except Exception: continue
    hits=[e for e in entries if "TRANSFORMERS" in e["full_path"].upper() and e["full_path"].upper().endswith((".DTX",".CFG",".PNG",".TGA"))]
    if hits:
        print("##",idx)
        for e in hits[:40]: print("  ",e["full_path"],e["size"])
