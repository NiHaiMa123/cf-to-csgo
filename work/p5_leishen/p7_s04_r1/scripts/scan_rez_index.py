# -*- coding: utf-8 -*-
"""Scan all REZ main indexes for FoxHowl/renewal arm texture names."""
import sys
from pathlib import Path
sys.path.insert(0, r"D:\project\cf_to_csgo\scripts\material_recovery")
import n05a_decoder_provenance_audit as audit

CF = audit.CF
KEYS = ("FOXHOWL", "FVIEW_HAND_FH", "FVIEW_ARM_FH", "FH_HAND", "FVIEW_HAND_RENEWAL", "ARM_FOX")
rezdir = CF / "rez"
for idx in sorted(rezdir.glob("*.rez")) + sorted(rezdir.glob("*.REZ")):
    try:
        entries = audit.read_rez_index_mmap(idx)
    except Exception as e:
        print(idx.name, "ERR", str(e)[:60]); continue
    hits = [e for e in entries if any(k in e["full_path"].upper() for k in KEYS) and e["full_path"].upper().endswith((".DTX",".TGA",".CFG"))]
    if hits:
        print("##", idx.name, len(entries), "entries")
        for e in hits[:40]:
            print("  ", e["full_path"], e["size"])
