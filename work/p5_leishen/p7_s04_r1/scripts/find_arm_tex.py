# -*- coding: utf-8 -*-
"""Find FoxHowl arm/hand DTX textures in the real REZ shards and decode previews."""
import sys, json
from pathlib import Path
sys.path.insert(0, r"D:\project\cf_to_csgo\scripts\material_recovery")
import n05a_decoder_provenance_audit as audit
from rez_verified_payload import read_verified_payload

OUT = Path(r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\source\armtex")
OUT.mkdir(parents=True, exist_ok=True)
CF = audit.CF  # D:\Program Files\CF(2)

# 1. scan indexes for candidate arm/hand/foxhowl texture names
cands = {}
for rez in ["rf016.rez", "rf017.rez", "rf015.rez", "rf014.rez"]:
    idx = CF / "rez" / rez
    if not idx.exists():
        print("missing", idx); continue
    entries = audit.read_rez_index_mmap(idx)
    hits = [e for e in entries if any(k in e["full_path"].upper() for k in
            ("FVIEW_HAND_FH", "FVIEW_ARM_FH", "FH_HAND", "FH_ARM",
             "FOXHOWL", "FOX_", "FVIEW_HAND_RENEWAL", "ARM_W", "RENEWAL"))]
    print(rez, len(entries), "entries,", len(hits), "hits")
    for e in hits:
        cands[e["full_path"]] = (idx, e)
        print("  ", e["full_path"], "size", e["size"])
